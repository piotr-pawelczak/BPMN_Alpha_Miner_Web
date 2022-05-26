"""
Module for handling loading log files (.csv, .xes)
"""

import pm4py
import pandas as pd


class LogLoader:

    def __init__(self, log_path, case_id_column_name='Case ID', activity_column_name='Activity',
                 timestamp_column_name='Start Timestamp'):
        self.log_path = log_path
        self.activity_column_name = activity_column_name
        self.case_id_column_name = case_id_column_name
        self.timestamp_column_name = timestamp_column_name
        self.log_df = self.read_logs()

    def read_logs(self):
        if self.log_path.endswith('.csv'):
            log_df = pd.read_csv(self.log_path)
            return log_df

        elif self.log_path.endswith('.xes'):
            log = pm4py.read_xes(self.log_path)
            log_df = pm4py.convert_to_dataframe(log)
            return log_df
        else:
            raise UnsupportedFileExtension(
                f'File {self.log_path} has unsupported extension. Try load .csv or .xes file')

    def get_variants(self):
        variants = self.log_df.sort_values(
            by=['Case ID', 'Start Timestamp']).groupby(['Case ID']).agg({'Activity': ";".join})
        variants.drop_duplicates(subset='Activity', keep=False, inplace=True)
        variants['Trace'] = [trace.split(';') for trace in variants['Activity']]
        return variants['Trace'].tolist()

    def get_event_count(self):
        ev_counter = self.log_df.Activity.value_counts()
        return ev_counter

    def pick_columns(self):

        if self.activity_column_name != 'Activity' and 'Activity' in self.log_df.columns:
            self.log_df.rename(columns={'Activity': 'not_selected_activity'}, inplace=True)

        self.log_df.rename(columns=
                           {self.activity_column_name: 'Activity',
                            self.case_id_column_name: 'Case ID',
                            self.timestamp_column_name: 'Start Timestamp'},
                           inplace=True)
        self.log_df = self.log_df[['Case ID', 'Activity', 'Start Timestamp']]


class UnsupportedFileExtension(Exception):
    """
    Custom exception for handling invalid file extension
    """
    pass
