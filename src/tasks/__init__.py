import os
import pathlib
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


events_dot_yaml_file_path = os.path.join(
    pathlib.Path(__file__).parent.resolve(),
    'events.yaml'
)

# Update plans in Stripe
with open(events_dot_yaml_file_path) as f:
    event_collection = load(f, Loader=Loader)

