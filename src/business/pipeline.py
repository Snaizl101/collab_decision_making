class Pipeline:
    def __init__(self,
                 audio_processor: AudioProcessor,
                 transcriber: Transcriber,
                 topic_analyzer: TopicAnalyzer):
        self.steps = [
            audio_processor,
            transcriber,
            topic_analyzer
        ]

    def process(self, context: AnalysisContext) -> AnalysisContext:
        for step in self.steps:
            context = step.process(context)
        return context