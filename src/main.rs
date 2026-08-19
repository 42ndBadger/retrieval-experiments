use clap::{Parser, Subcommand, ValueEnum};
use retrieval_experiments::benchmark::{
    ConstructionResult, QueryResult, construction_benchmark, query_benchmark,
};
use retrieval_experiments::measurement_writer::{
    MeasurementInfo, MeasurementType, write_measurement,
};
use serde::Serialize;
use serde_json::json;
use std::collections::HashMap;
use std::fs;

use consensus_retrieval::ConsensusRetrieval;
use retrieval_experiments::caramel::CsfU32;

use retrieval_experiments::data_gen;
use retrieval_experiments::data_gen::Distribution;

#[derive(Parser)]
#[command(version, about, long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Command,
}
#[derive(Subcommand, Debug, Clone)]
enum Command {
    Gen {
        distribution: DistributionSelection,
        #[arg(short)]
        n: usize,
        #[arg(short, default_value = "0.5")]
        p: f64,
        #[arg(long, default_value = "10")]
        bound: u64,
        #[arg(short, long, default_value = "data.kv")]
        file: String,
    },
    Bench {
        #[arg(short, long)]
        algorithm: Algorithm,
        #[arg(short, long)]
        input: String,
        #[arg(short, long)]
        output: String,
        #[arg(short, long, default_value = "1")]
        construction_repetitions: usize,
        #[arg(short, long, default_value = "1000")]
        query_repetitions: usize,
        #[arg(short = 'P', long = "param", action = clap::ArgAction::Append)]
        params: Vec<String>,
    },
}

#[derive(Debug, Clone, Copy, ValueEnum)]
enum DistributionSelection {
    Uniform,
    TruncatedGeometric,
    Bernoulli,
}

#[derive(Debug, Clone, Copy, ValueEnum)]
enum Algorithm {
    Consensus,
    Caramel,
}

fn parse_params(raw: &[String]) -> HashMap<String, String> {
    let mut map = HashMap::new();
    for entry in raw {
        let (k, v) = entry
            .split_once('=')
            .unwrap_or_else(|| panic!("expected key=value, got {entry:?}"));
        map.insert(k.to_string(), v.to_string());
    }
    map
}

fn main() {
    let cli = Cli::parse();
    match &cli.command {
        Command::Gen {
            distribution,
            n,
            p,
            bound,
            file,
        } => {
            let distribution = match distribution {
                DistributionSelection::Uniform => Distribution::Uniform { max: *bound },
                DistributionSelection::TruncatedGeometric => {
                    Distribution::TruncatedGeometric { p: *p, max: *bound }
                }
                DistributionSelection::Bernoulli => Distribution::Bernoulli { p: *p },
            };
            let data = data_gen::string_keys(*n)
                .into_iter()
                .zip(distribution.generate_values(*n))
                .map(|(k, v)| format!("{k} {v}"))
                .collect::<Vec<String>>()
                .join("\n");

            fs::write(file, data).expect(&format!("failed to write data to {file}"));
        }
        Command::Bench {
            algorithm,
            input,
            output,
            construction_repetitions,
            query_repetitions,
            params,
        } => {
            let input_data = fs::read_to_string(input).expect("failed to read input file");
            let kv = input_data
                .lines()
                .map(|l| l.split_once(' ').unwrap())
                .map(|(k, v)| (k, v.parse::<u32>().unwrap()))
                .collect::<Vec<_>>();

            let algo_params = parse_params(params);

            let (construction_results, query_results, param): (
                Box<dyn Iterator<Item = Box<dyn erased_serde::Serialize>>>,
                _,
                _,
            ) = match algorithm {
                Algorithm::Consensus => {
                    let consensus_params = consensus_retrieval::parameters::Parameters {
                        avg_group_load: algo_params
                            .get("avg_group_load")
                            .map(|v| v.parse().expect("avg_group_load must be f64"))
                            .expect("consensus requires --param avg_group_load=<f64>"),
                        inital_group_width: algo_params
                            .get("inital_group_width")
                            .map(|v| v.parse().expect("inital_group_width must be usize"))
                            .expect("consensus requires --param inital_group_width=<usize>"),
                        insertion_increment: algo_params
                            .get("insertion_increment")
                            .map(|v| v.parse().expect("insertion_increment must be usize"))
                            .expect("consensus requires --param insertion_increment=<usize>"),
                        max_difficulty_of_task: algo_params
                            .get("max_difficulty_of_task")
                            .map(|v| v.parse().expect("max_difficulty_of_task must be f64"))
                            .expect("consensus requires --param max_difficulty_of_task=<f64>"),
                        max_difficulty_at_group_border: algo_params
                            .get("max_difficulty_at_group_border")
                            .map(|v| {
                                v.parse()
                                    .expect("max_difficulty_at_group_border must be f64")
                            })
                            .expect(
                                "consensus requires --param max_difficulty_at_group_border=<f64>",
                            ),
                    };
                    let param_json = json!({
                        "avg_group_load": consensus_params.avg_group_load,
                        "inital_group_width": consensus_params.inital_group_width,
                        "insertion_increment": consensus_params.insertion_increment,
                        "max_difficulty_of_task": consensus_params.max_difficulty_of_task,
                        "max_difficulty_at_group_border": consensus_params.max_difficulty_at_group_border,
                    });
                    let constr = construction_benchmark::<ConsensusRetrieval<&str, u32>>(
                        *construction_repetitions,
                        &kv,
                        &consensus_params,
                    );
                    let query = query_benchmark::<ConsensusRetrieval<&str, u32>>(
                        *query_repetitions,
                        &kv,
                        &consensus_params,
                    );

                    (
                        Box::new(constr.into_iter().map(|x| Box::new(x) as _)),
                        query,
                        param_json,
                    )
                }
                Algorithm::Caramel => {
                    let constr =
                        construction_benchmark::<CsfU32>(*construction_repetitions, &kv, &());
                    let query = query_benchmark::<CsfU32>(*query_repetitions, &kv, &());
                    (
                        Box::new(constr.into_iter().map(|x| Box::new(x) as _)),
                        query,
                        json!(()),
                    )
                }
            };

            let config = MeasurementInfo {
                m_type: MeasurementType::Construction,
                n_iters: *construction_repetitions,
                input_size: kv.len(),
                input_file_name: input.clone(),
                params: param.clone(),
            };

            write_measurement(
                config,
                construction_results,
                fs::File::create(output.clone() + ".construction.json")
                    .expect(&format!("could not open output file {output}")),
            )
            .expect("writing failed");

            let config = MeasurementInfo {
                m_type: MeasurementType::Query,
                n_iters: *query_repetitions,
                input_size: kv.len(),
                input_file_name: input.clone(),
                params: param,
            };

            write_measurement(
                config,
                query_results,
                fs::File::create(output.clone() + ".query.json")
                    .expect(&format!("could not open output file {output}")),
            )
            .expect("writing failed");
        }
    }
}
