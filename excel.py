import cv2
import pandas as pd
from datetime import datetime
from deepface import DeepFace

# Initialize Excel file setup
excel_filename = "output.xlsx"
columns = ["Identity", "Similarity", "Date", "Time"]
data = []

# Initialize video capture with higher resolution
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# Verify resolution
print(f"Camera resolution: {cap.get(3)}x{cap.get(4)}")

registered_names = set()
print("Streaming started. Press 'q' or 'Q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    try:
        results = DeepFace.find(frame, db_path="db", enforce_detection=False)
        if results and len(results) > 0:
            df = results[0]
            if not df.empty:
                top_match = df.iloc[0]
                identity = top_match["identity"]
                similarity = top_match.get("VGG-Face_cosine", "N/A")

                now = datetime.now()
                if identity not in registered_names:
                    registered_names.add(identity)
                    data.append([
                        identity,
                        similarity,
                        now.strftime("%Y-%m-%d"),
                        now.strftime("%H:%M:%S")
                    ])
                    print(f"Registered: {identity} | Similarity: {similarity} | {now}")
    except Exception as e:
        print("DeepFace error:", e)

    cv2.imshow("Capturing", frame)
    if cv2.waitKey(1) & 0xFF in [ord('q'), ord('Q')]:
        break

cap.release()
cv2.destroyAllWindows()

# Save collected data to Excel
df_output = pd.DataFrame(data, columns=columns)
df_output.to_excel(excel_filename, index=False)

print(f"Output saved to '{excel_filename}'")
