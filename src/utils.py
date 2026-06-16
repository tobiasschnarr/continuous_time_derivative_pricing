import os
import pandas as pd


def load_svensson_params(folder_path: str) -> pd.DataFrame:
    """
    Load Bundesbank Svensson yield-curve parameters and merge them by date.
    Bundesbank files use decimal dots, not German decimal commas.
    """

    param_files = {
        "beta0.csv": "beta0",
        "beta1.csv": "beta1",
        "beta2.csv": "beta2",
        "beta3.csv": "beta3",
        "tau1.csv": "tau1",
        "tau2.csv": "tau2",
    }

    svensson_df = None
    date_pattern = r"^\d{4}-\d{2}-\d{2}$"

    for filename, parameter_name in param_files.items():
        path = os.path.join(folder_path, filename)

        raw_df = pd.read_csv(
            path,
            delimiter=",",
            header=None,
            skip_blank_lines=True,
        )

        param_df = raw_df[raw_df[0].astype(str).str.match(date_pattern)].copy()

        param_df[0] = pd.to_datetime(param_df[0], format="%Y-%m-%d")
        param_df = param_df.rename(columns={0: "Datum", 1: parameter_name})
        param_df = param_df[["Datum", parameter_name]]

        param_df[parameter_name] = pd.to_numeric(
            param_df[parameter_name],
            errors="coerce",
        )

        if svensson_df is None:
            svensson_df = param_df
        else:
            svensson_df = svensson_df.merge(param_df, on="Datum", how="inner")

    return svensson_df.sort_values("Datum").reset_index(drop=True)