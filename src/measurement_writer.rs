use std::io::Write;

use serde::Serialize;
use serde_json::Value;

#[derive(Debug, Serialize)]
pub struct MeasurementInfo {
    m_type: MeasurementType,
    params: Value,
}

#[derive(Debug, Serialize)]
pub enum MeasurementType {
    Query,
    Construction,
}

fn write_measurement(
    config: impl Serialize,
    measurements: Vec<impl Serialize>,
    mut writer: impl Write,
) -> anyhow::Result<()> {
    serde_json::to_writer(&mut writer, &config)?;
    writeln!(&mut writer, "")?;

    let mut writer = csv::Writer::from_writer(&mut writer);
    for mes in measurements {
        writer.serialize(mes)?;
    }
    Ok(())
}
