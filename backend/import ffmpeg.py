import ffmpeg
def webmd_to_mp3(input_path, out_path):
    return ffmpeg.input("input.webm").output("output.mp3").run()
output = "output.mp3"
webmd_to_mp3(r"C:\Users\teemo\OneDrive - Stellenbosch University\Desktop\Hackathon\patient-data-app\backend\patients\PT-2024-001\recordings\1755356737767.webm", "output.mp3")