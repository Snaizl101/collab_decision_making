class AudioProcessor:
    def process(self, input_dir, output_dir):
        print(f"Dummy processor: Would process files from {input_dir} to {output_dir}")

    def generate_report(self, session_id, format):
        print(f"Dummy processor: Would generate {format} report for session {session_id}")

    def get_status(self, session_id=None):
        return f"Dummy processor: Status for session {session_id if session_id else 'all'}"