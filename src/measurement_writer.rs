use std::io::Write;

use serde::Serialize;
use serde_json::Value;

fn write_measurement(
    config: impl Serialize,
    measurements: Vec<impl Serialize>,
    writer: &mut impl Write,
) -> anyhow::Result<()> {
    serde_json::to_writer(writer, &config)?;
    writeln!(writer, "")?;

    let mut writer = csv::Writer::from_writer(writer);
    for mes in measurements {
        writer.serialize(mes)?;
    }
    Ok(())
}
