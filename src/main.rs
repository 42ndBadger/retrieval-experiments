use clap::{Parser, Subcommand, ValueEnum};
use retrieval_experiments::benchmark::{construction_benchmark, query_benchmark};
use retrieval_experiments::measurement_writer::{
    MeasurementInfo, MeasurementType, write_measurement,
};
use serde_json::json;
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
        } => {
            let input_data = fs::read_to_string(input).expect("failed to read input file");
            let kv = input_data
                .lines()
                .map(|l| l.split_once(' ').unwrap())
                .map(|(k, v)| (k, v.parse::<u32>().unwrap()))
                .collect::<Vec<_>>();

            let (construction_results, query_results, param) = match algorithm {
                Algorithm::Consensus => (
                    construction_benchmark::<ConsensusRetrieval<&str, u32>>(
                        *construction_repetitions,
                        &kv,
                        &20,
                    ),
                    query_benchmark::<ConsensusRetrieval<&str, u32>>(*query_repetitions, &kv, &20),
                    json!(20),
                ),
                Algorithm::Caramel => (
                    construction_benchmark::<CsfU32>(*construction_repetitions, &kv, &()),
                    query_benchmark::<CsfU32>(*query_repetitions, &kv, &()),
                    json!(()),
                ),
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
