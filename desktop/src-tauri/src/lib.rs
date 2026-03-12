use std::process::Command;

#[tauri::command]
fn pick_folder() -> Result<Option<String>, String> {
    #[cfg(target_os = "macos")]
    {
        let output = Command::new("osascript")
            .args([
                "-e",
                r#"POSIX path of (choose folder with prompt "Choose a folder to trust in Relevect")"#,
            ])
            .output()
            .map_err(|error| format!("Failed to open the folder picker: {error}"))?;

        if output.status.success() {
            let path = String::from_utf8_lossy(&output.stdout).trim().to_string();
            if path.is_empty() {
                Ok(None)
            } else {
                Ok(Some(path.trim_end_matches('/').to_string()))
            }
        } else {
            let stderr = String::from_utf8_lossy(&output.stderr);
            if stderr.contains("-128") {
                Ok(None)
            } else {
                Err(format!(
                    "Folder picker failed: {}",
                    stderr.trim().trim_matches('"')
                ))
            }
        }
    }

    #[cfg(not(target_os = "macos"))]
    {
        Err("Native folder selection is not implemented on this platform yet.".to_string())
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![pick_folder])
        .run(tauri::generate_context!())
        .expect("error while running Relevect desktop");
}
