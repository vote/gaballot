from datadog import DogStatsd

class GAStatsd(DogStatsd):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.constant_tags = self.constant_tags + ["env:prod"]


statsd = GAStatsd()
