# Use the official ROS Noetic image from the Docker Hub
FROM ros:noetic-ros-core

# Install Python, pip, and other necessary dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip

RUN pip3 install --no-cache-dir --extra-index-url https://rospypi.github.io/simple/ rospy rosbag h5py==3.1.0 numpy tqdm

# Copy the current directory contents into /e2calib
COPY . /e2calib

WORKDIR /e2calib/python

# Source the ROS setup script and start a bash shell
ENTRYPOINT ["/bin/bash", "-c", "source /opt/ros/noetic/setup.bash && exec bash"]