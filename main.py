import sys
import numpy as np
import sounddevice as sd
import soundfile as sf
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout
from PyQt5.QtCore import pyqtSlot
from openai import OpenAI
import time
import os
from dotenv import load_dotenv
from todoist_commands import TodoistAssistant
import requests
class Recorder:
    def __init__(self, filename='output.wav', samplerate=44100, channels=1, device=None):
        """
        Initializes the Recorder class.

        :param filename: The name of the file to save the recording.
        :param samplerate: The sampling rate of the recording.
        :param channels: Number of audio channels (1 for mono, 2 for stereo).
        :param device: The input device ID. Set to None to use the default input device.
        """
        self.filename = filename
        self.samplerate = samplerate
        self.channels = channels
        self.device = device  # None uses the default input device
        self.is_recording = False
        self.recording = []
        self.stream = None

    def start_recording(self):
        """Starts the audio recording."""
        if self.is_recording:
            print("Already recording.")
            return
        self.is_recording = True
        self.recording = []
        print("Recording started.")

        def callback(indata, frames, time, status):
            if status:
                print(f"Recording status: {status}")
            if self.is_recording:
                if indata.size > 0:
                    self.recording.append(indata.copy())
                else:
                    print("Received empty audio data.")

        try:
            self.stream = sd.InputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                callback=callback,
                device=self.device  # None uses the default input device
            )
            self.stream.start()
        except Exception as e:
            print(f"Failed to start recording: {e}")
            self.is_recording = False

    def stop_recording(self):
        """Stops the audio recording and saves the file."""
        if not self.is_recording:
            print("Not currently recording.")
            return
        self.is_recording = False
        print("Recording stopped.")

        try:
            self.stream.stop()
            self.stream.close()
        except Exception as e:
            print(f"Failed to stop recording: {e}")

        try:
            if self.recording:
                audio_data = np.concatenate(self.recording, axis=0)
                # Optionally normalize the audio data
                # audio_data = audio_data / np.max(np.abs(audio_data))
                sf.write(self.filename, audio_data, self.samplerate)
                print(f"Recording saved to '{self.filename}'")
            else:
                print("No audio data recorded.")
        except ValueError as e:
            print(f"No audio data to write: {e}")
        except Exception as e:
            print(f"Error saving recording: {e}")

        self.recording = []

class VoiceRecorderApp(QWidget):
    def __init__(self, recorder):
        """
        Initializes the PyQt5 application.

        :param recorder: An instance of the Recorder class.
        """
        super().__init__()
        self.recorder = recorder
        self.init_ui()

    def init_ui(self):
        """Sets up the user interface."""
        self.setWindowTitle('Voice Recorder')

        layout = QVBoxLayout()

        self.start_button = QPushButton('Start Recording')
        self.start_button.clicked.connect(self.recorder.start_recording)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton('Stop Recording')
        self.stop_button.clicked.connect(self.stop_and_close)
        layout.addWidget(self.stop_button)

        self.setLayout(layout)
        self.show()

    @pyqtSlot()
    def stop_and_close(self):
        """Stops the recording and closes the application."""
        self.recorder.stop_recording()
        print("Closing application.")
        QApplication.instance().quit()
def transcribe_audio(filename="output.wav"):
    try:
        # Specify the URL where the file will be uploaded
        url = "https://hello-world.ebaadforrandomstuff.workers.dev/"

        # Open the voice file in binary mode
        with open(filename, "rb") as audio_file:
            # Create the files dictionary for the POST request
            files = {
                "file": ("voice_file.wav", audio_file, "audio/wav")
            }

            # Make the POST request with the file
            response = requests.post(url, files=files)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Process the server's response
            # Assuming the server returns JSON with a 'text' field
            transcription = response.json()
            print(transcription['text'])
            return transcription['text']
    except Exception as e:
        print(f"An error occurred during transcription: {e}")
        return None
def main():
    # Initialize the recorder without specifying a device ID to use the default input device
    recorder = Recorder(filename='output.wav', samplerate=44100, channels=1, device=None)

    app = QApplication(sys.argv)
    window = VoiceRecorderApp(recorder)
    app.exec_()  # Removed sys.exit()
    return recorder

if __name__ == "__main__":
    load_dotenv()
    todoist_api_key = os.getenv("TODOIST_API_KEY")    
    
    # Create assistant instance
    assistant = TodoistAssistant(todoist_api_key)
    
    print("🎉 Welcome to TodoList Manager! 🎉")
    
    filter_options = {
        1: "overdue",
        2: "today | 7 days",
        3: "all",
    }

    while True:
        try:
            print("Please select a filter option:")
            for number, description in filter_options.items():
                print(f"{number}. {description.capitalize()}")
            print("4. Enter your own filter(look at todoist documentation)")
            choice = input("Enter the number of your choice (or 0 to exit): ")

            if choice.isdigit():
                choice = int(choice)
                if choice == 0:
                    print("Exiting TodoList Manager. Goodbye! 👋")
                    break
                elif choice in filter_options:
                    filter_query = filter_options[choice]
                elif choice == 4:
                    filter_query = input("Enter your custom filter query: ")
                else:
                    print("Invalid choice. Please enter a number between 0 and 7.")
                    continue
            else:
                print("Invalid input. Please enter a valid number.")
                continue

            try:
                assistant.get_tasks(filter_query)
            except Exception as e:
                if "400 Client Error" in str(e):
                    print("Error fetching tasks: Invalid filter query. Please try again with a valid filter.")
                else:
                    print(f"An unexpected error occurred: {e}")
                continue

            
            print("Get ready to record - a popup window will appear!")
            time.sleep(1)
            recorder = main()
            user_input = transcribe_audio(recorder.filename)
            assistant.run(user_input)

        except ValueError:
            print("Invalid input. Please enter a valid number.")