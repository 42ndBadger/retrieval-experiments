use clap::{Parser, Subcommand, ValueEnum};
use data_gen::Distribution;
use std::fs;

mod data_gen;

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
        algorithm: String,
        input: String,
        output: String,
    },
}

#[derive(Debug, Clone, Copy, ValueEnum)]
enum DistributionSelection {
    Uniform,
    TruncatedGeometric,
    Bernoulli,
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
        } => {
            todo!("benchmarking not yet implemented")
        }
    }
}
