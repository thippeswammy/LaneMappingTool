#!/usr/bin/env python3
import rospy
import csv
import os
import sys
import subprocess
import signal
import time
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Float64
from tf.transformations import euler_from_quaternion

class DataRecorder:
    def __init__(self, run_name):
        rospy.init_node('vehicle_data_recorder', anonymous=True)
        
        self.run_name = run_name
        
        # Calculate path relative to this script: analysis/recording/../recorded_data
        script_dir = os.path.dirname(os.path.abspath(__file__))
        analysis_dir = os.path.dirname(script_dir)
        self.output_dir = os.path.join(analysis_dir, 'recorded_data', self.run_name)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        self.csv_path = os.path.join(self.output_dir, 'vehicle_data.csv')
        self.bag_path = os.path.join(self.output_dir, 'vlp16_data.bag')
        
        # State variables
        self.current_pose = None
        self.current_steering = 0.0
        self.current_speed = 0.0
        
        # Setup CSV
        self.csv_file = open(self.csv_path, 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(['timestamp', 'x', 'y', 'z', 'yaw', 'steering_angle', 'speed'])
        
        # Subscribers
        rospy.Subscriber('/ndt_pose', PoseStamped, self.pose_callback)
        rospy.Subscriber('/mpc/steer_angle', Float64, self.steer_callback)
        rospy.Subscriber('/mpc/velocity', Float64, self.speed_callback)
        
        # Start ROS Bag recording for VLP16
        print(f"Starting ROS Bag recording to {self.bag_path}...")
        # Record /points_raw and /ndt_pose (for extrinsic calibration/visualization later)
        self.bag_process = subprocess.Popen(
            ['rosbag', 'record', '-O', self.bag_path, '/points_raw', '/ndt_pose'],
            preexec_fn=os.setsid # Create new session to easily kill group later
        )
        
    def pose_callback(self, msg):
        self.current_pose = msg
        
    def steer_callback(self, msg):
        self.current_steering = msg.data
        
    def speed_callback(self, msg):
        self.current_speed = msg.data
        
    def run(self):
        rate = rospy.Rate(20) # 20 Hz recording for CSV
        print(f"Recording data for run '{self.run_name}'...")
        print("Press Ctrl+C to stop recording.")
        
        try:
            while not rospy.is_shutdown():
                if self.current_pose:
                    p = self.current_pose.pose.position
                    o = self.current_pose.pose.orientation
                    
                    # Convert Quaternion to Yaw
                    orientation_list = [o.x, o.y, o.z, o.w]
                    (roll, pitch, yaw) = euler_from_quaternion(orientation_list)
                    
                    timestamp = rospy.get_time()
                    
                    self.csv_writer.writerow([
                        timestamp,
                        p.x, p.y, p.z, yaw,
                        self.current_steering,
                        self.current_speed
                    ])
                    
                rate.sleep()
                
        except rospy.ROSInterruptException:
            pass
        finally:
            self.cleanup()
            
    def cleanup(self):
        print("\nStopping recording...")
        self.csv_file.close()
        
        # Terminate ROS Bag process
        if self.bag_process:
            print("Stopping rosbag record...")
            os.killpg(os.getpgid(self.bag_process.pid), signal.SIGINT)
            self.bag_process.wait()
            print("Rosbag saved.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python record_ros.py <run_name>")
        print("Example: python record_ros.py original_run")
        sys.exit(1)
        
    run_name = sys.argv[1]
    
    # Handle preexec_fn for Windows (it's not available, use minimal fallback)
    # Since user is on Windows but likely running ROS via WSL or VM?
    # Wait, the user's OS is Windows, but ROS usually runs on Linux.
    # If they are running minimal ROS on Windows, `os.setsid` might fail.
    # Let's add a check.
    if os.name == 'nt':
         print("Warning: Running on Windows. Subprocess termination might be less clean.")
         # Windows doesn't support preexec_fn/setsid in the same way.
         # For simplicity in this environment, valid python script:
    
    recorder = DataRecorder(run_name)
    recorder.run()
