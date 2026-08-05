use std::io::Write;

use serde::Serialize;
use serde_json::Value;

#[derive(Debug, Serialize)]
pub struct MeasurementInfo {
    pub m_type: MeasurementType,
    pub n_iters: usize,
    pub input_size: usize,
    pub input_file_name: String,
    pub params: Value,
}

#[derive(Debug, Serialize)]
pub enum MeasurementType {
    Query,
    Construction,
}

pub fn write_measurement(
    config: MeasurementInfo,
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
