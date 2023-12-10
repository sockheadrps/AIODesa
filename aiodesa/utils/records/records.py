def build_records(*data_classes):
    class Records:
        def __init__(self) -> None:
            for data_cls in data_classes:
                setattr(Records, data_cls.__name__, data_cls)

    return Records
