class Activity:
    def __init__(self, id, key, type, start_time=None, end_time=None):
        self.id = id
        self.key = key
        self.type = type
        self.start_time = start_time
        self.end_time = end_time

    def to_dict(self):
        return {
            "id": self.id,
            "key": self.key,
            "type": self.type,
            "start_time": self.start_time,
            "end_time": self.end_time
        }

    def copy(self):
        """
        Creates a copy of this Activity instance.
        """
        return Activity(
            id=self.id,
            key=self.key,
            type=self.type,
            start_time=self.start_time,
            end_time=self.end_time
        )

    @staticmethod
    def from_dict(data):
        return Activity(
            id=data.get("id"),
            key=data.get("key"),
            type=data.get("type"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time")
        )

    def __repr__(self):
        return f"Activity(id={self.id}, key='{self.key}', type='{self.type}', start_time={self.start_time}, end_time={self.end_time})"
