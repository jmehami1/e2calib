from pathlib import Path
import tqdm
import rosbag
from data.accumulator import EventAccumulatorRos

    
def get_first_message(bag_file, topic):
    """
    Function to extract the first message from a specified topic in a ROS bag file.
    """
    with rosbag.Bag(str(bag_file), 'r') as bag:
        for topic_name, msg, t in bag.read_messages(topics=[topic]):
            # Return the first message found
            return topic_name, msg, t
    return None, None, None


def extract_events_start_end(events, t_start, t_end):
    t_all_ns = [event.ts.to_nsec() for event in events]
    mask = [ t >= t_start and t < t_end for t in t_all_ns]
    events_extracted = [d for d, m in zip(events, mask) if m]
    last_event_extracted = mask[-1]
    return events_extracted, last_event_extracted


def ev_generator(bagpath: Path, delta_t_ms: int=1000, topic: str='/dvs/events'):
    assert bagpath.exists()
    assert bagpath.suffix == '.bag'

    delta_t_ns = delta_t_ms * 10**6

    msg_first = get_first_message(bagpath, topic)[1]
    t_start_ns = msg_first.events[0].ts.to_nsec()
    t_ev_acc_end_ns = t_start_ns + delta_t_ns
    ev_acc = EventAccumulatorRos()

    with rosbag.Bag(str(bagpath), 'r') as bag:
        pbar = tqdm.tqdm(total=bag.get_message_count(topic))
        for _, msg, _ in bag.read_messages(topics=[topic]):
            events_extracted, last_event_extracted = extract_events_start_end(msg.events, t_start_ns, t_ev_acc_end_ns)

            if events_extracted is not None:
                ev_acc.add_events(events_extracted)

            if not last_event_extracted:
                t_start_ns = t_start_ns + delta_t_ns
                t_ev_acc_end_ns = t_ev_acc_end_ns + delta_t_ns

                events = ev_acc.get_events()
                yield events
                ev_acc = EventAccumulatorRos()

            pbar.update(1)
