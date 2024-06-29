from ast import arg
from pathlib import Path
import tqdm
import rosbag
from data.accumulator import EventAccumulatorRos
import multiprocessing
import threading
import queue




    
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


# def read_events_from_msg(msg):
#     # Read some data from the bag file and store in a python list
#     events = []
#     for _, msg, _ in bag.read_messages(topic):
#         events.extend(msg.events)
#     return events

def read_messages(bag, topic, msg_queue, stop_event):
    # Read messages from the bag file and put them in the queue
    for _, msg, _ in bag.read_messages(topics=[topic]):
        if stop_event.is_set():
            break
        msg_queue.put(msg)
    bag.close()
    msg_queue.put(None)  # Sentinel to signal the end of messages


def ev_generator(bagpath: Path, delta_t_ms: int=1000, topic: str='/dvs/events'):
    assert bagpath.exists()
    assert bagpath.suffix == '.bag'

    
    msg_first = get_first_message(bagpath, topic)[1]

    msg_queue = queue.Queue(maxsize=1000)  # Adjust size as needed
    stop_event = threading.Event()

    bag = rosbag.Bag(str(bagpath), 'r')

    reader_thread = threading.Thread(target=read_messages, args=(bag, topic, msg_queue, stop_event))
    reader_thread.start()

    delta_t_ns = delta_t_ms * 10**6
    t_start_ns = msg_first.events[0].ts.to_nsec()
    t_ev_acc_end_ns = t_start_ns + delta_t_ns
    ev_acc = EventAccumulatorRos()
    pbar = tqdm.tqdm(total=bag.get_message_count(topic), desc="Extracting messages", unit="msg")

    # Process messages from the queue in parallel
    while True:
        msg = msg_queue.get()
        if msg is None:
            break

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

    
    # Signal the reader thread to stop
    stop_event.set()
    reader_thread.join()



#         result = pool.apply_async(worker, args=(msg,))
#         results.append(result)




#  for _, msg, _ in bag.read_messages(topics=[topic]):
#             events_extracted, last_event_extracted = extract_events_start_end(msg.events, t_start_ns, t_ev_acc_end_ns)

#             if events_extracted is not None:
#                 ev_acc.add_events(events_extracted)

#             if not last_event_extracted:
#                 t_start_ns = t_start_ns + delta_t_ns
#                 t_ev_acc_end_ns = t_ev_acc_end_ns + delta_t_ns

#                 events = ev_acc.get_events()
#                 yield events
#                 ev_acc = EventAccumulatorRos()

#     # Ensure all results are processed
#     for result in results:
#         print(result.get())



#     with rosbag.Bag(str(bagpath), 'r') as bag:

#         events = []
#         pbar = tqdm.tqdm(total=bag.get_message_count(topic), desc="Extracting messages", unit="msg")
#         for _, msg, _ in bag.read_messages(topics=[topic]):
#             events.extend(msg.events)
#             pbar.update(1)

        





#         # with multiprocessing.Pool() as pool:
#         #     for data in pool.imap_unordered(lambda args: read_events_from_bag(*args), [bag, topic]):
#         #         # Store data to dataset
#         #         if data is not None:
#         #             dataset.append(data)
#         for _, msg, _ in bag.read_messages(topics=[topic]):
#             events_extracted, last_event_extracted = extract_events_start_end(msg.events, t_start_ns, t_ev_acc_end_ns)

#             if events_extracted is not None:
#                 ev_acc.add_events(events_extracted)

#             if not last_event_extracted:
#                 t_start_ns = t_start_ns + delta_t_ns
#                 t_ev_acc_end_ns = t_ev_acc_end_ns + delta_t_ns

#                 events = ev_acc.get_events()
#                 yield events
#                 ev_acc = EventAccumulatorRos()

#             pbar.update(1)
