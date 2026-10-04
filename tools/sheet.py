"""Planche contact : python tools_sheet.py out.png img1 img2 ... (4 colonnes)."""
import sys
import cv2
import numpy as np
out, files = sys.argv[1], sys.argv[2:]
cols = 3 if len(files) <= 9 else 4
w = 1920 // cols
h = w * 9 // 16
rows = (len(files) + cols - 1) // cols
sheet = np.zeros((rows * (h + 4), cols * (w + 4), 3), np.uint8) + 40
for i, f in enumerate(files):
    im = cv2.resize(cv2.imread(f), (w, h), interpolation=cv2.INTER_AREA)
    lab = f.split('/')[-1].replace('.png', '')
    cv2.putText(im, lab, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1, cv2.LINE_AA)
    r, c = divmod(i, cols)
    sheet[r * (h + 4):r * (h + 4) + h, c * (w + 4):c * (w + 4) + w] = im
cv2.imwrite(out, sheet)
