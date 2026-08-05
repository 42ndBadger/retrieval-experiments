use clap::{Parser, Subcommand, ValueEnum};
use std::fs;

use retrieval_experiments::data_gen;
use retrieval_experiments::data_gen::Distribution;
use retrieval_experiments::instance::BenchmarkInstance;

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

            fs::write(file, data).expect("failed to write data to {file}");
        }
        Command::Bench {
            algorithm,
            input,
            output,
            construction_repetitions,
            query_repetitions,
        } => {
            let input = fs::read_to_string(input).expect("failed to read input file");
            let kv = input
                .lines()
                .map(|l| l.split_once(' ').unwrap())
                .map(|(k, v)| (k, v.parse::<u64>().unwrap()))
                .collect::<Vec<_>>();
        }
    }
}
