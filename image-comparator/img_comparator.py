import cv2, numpy as np
from skimage.metrics import structural_similarity as ssim
import json
from pathlib import Path

def to_gray(img_bgr):
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

def merge_boxes(boxes, iou_thresh=0.35, gap_thresh=50, expand=8):
    def to_xyxy(b):
        x,y,w,h = b; return (x, y, x+w, y+h)
    def iou(a,b):
        ax1,ay1,ax2,ay2 = to_xyxy(a); bx1,by1,bx2,by2 = to_xyxy(b)
        xi1, yi1 = max(ax1, bx1), max(ay1, by1)
        xi2, yi2 = min(ax2, bx2), min(ay2, by2)
        inter = max(0, xi2-xi1) * max(0, yi2-yi1)
        union = (ax2-ax1)*(ay2-ay1) + (bx2-bx1)*(by2-by1) - inter + 1e-9
        return inter/union
    def expand_box(b, m):
        x,y,w,h = b; return (x-m, y-m, w+2*m, h+2*m)
    def overlap_1d(a1,a2,b1,b2):
        return min(a2,b2) - max(a1,b1)
    def box_gap(a,b):
        ax1,ay1,ax2,ay2 = to_xyxy(a); bx1,by1,bx2,by2 = to_xyxy(b)
        # gap along x (0 if overlapping)
        gx = max(0, max(ax1,bx1) - min(ax2,bx2))
        # gap along y (0 if overlapping)
        gy = max(0, max(ay1,by1) - min(ay2,by2))
        return max(gx, gy), gx, gy

    boxes = sorted(boxes, key=lambda b: (b[1], b[0]))
    merged = []
    for b in boxes:
        merged_any = False
        # test with expanded versions (encourage merging)
        bE = expand_box(b, expand)
        for i,m in enumerate(merged):
            mE = expand_box(m, expand)
            if iou(bE, mE) > iou_thresh:
                # merge by enclosure
                x1 = min(b[0], m[0]); y1 = min(b[1], m[1])
                x2 = max(b[0]+b[2], m[0]+m[2]); y2 = max(b[1]+b[3], m[1]+m[3])
                merged[i] = (x1, y1, x2-x1, y2-y1)
                merged_any = True
                break
            # proximity rule: small gap and axis overlap
            gap, gx, gy = box_gap(b, m)
            ax1,ay1,ax2,ay2 = to_xyxy(b); mx1,my1,mx2,my2 = to_xyxy(m)
            overlap_x = overlap_1d(ax1, ax2, mx1, mx2)
            overlap_y = overlap_1d(ay1, ay2, my1, my2)
            if gap <= gap_thresh and (overlap_x > 0 or overlap_y > 0):
                x1 = min(b[0], m[0]); y1 = min(b[1], m[1])
                x2 = max(b[0]+b[2], m[0]+m[2]); y2 = max(b[1]+b[3], m[1]+m[3])
                merged[i] = (x1, y1, x2-x1, y2-y1)
                merged_any = True
                break
        if not merged_any:
            merged.append(b)
    return merged

def crop_with_pad(img, box, pad=24):
    h,w = img.shape[:2]
    x,y,bw,bh = box
    x1, y1 = max(0, x-pad), max(0, y-pad)
    x2, y2 = min(w, x+bw+pad), min(h, y+bh+pad)
    return img[y1:y2, x1:x2].copy(), (x1,y1,x2-x1,y2-y1)

def save_thumb(name, img, maxh=900):
    h,w = img.shape[:2]
    if h > maxh:
        img = cv2.resize(img, (int(w*maxh/h), maxh), interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(OUT / name), img)

if __name__ == "__main__":
    OUT = Path("image-comparator/out")
    OUT.mkdir(parents=True, exist_ok=True)

    before = cv2.imread('image-comparator/input/before.png')
    after  = cv2.imread('image-comparator/input/after.png')

    grayB, grayA = to_gray(before), to_gray(after)
    score, diff = ssim(grayB, grayA, full=True, gaussian_weights=True, use_sample_covariance=False)
    diff = (1.0 - diff)  # make “more different” = brighter

    # Heatmap for visualisation
    diff_u8 = np.clip(diff*255,0,255).astype('uint8')
    th = cv2.threshold(diff_u8, 0, 255, cv2.THRESH_OTSU)[0]
    binmask = (diff_u8 >= th).astype('uint8')*255
    binmask = cv2.morphologyEx(binmask, cv2.MORPH_CLOSE, np.ones((5,5),np.uint8), iterations=2)

    cnts = cv2.findContours(binmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts)==2 else cnts[1]
    boxes = [cv2.boundingRect(c) for c in cnts if cv2.contourArea(c) > 40]
    boxes = merge_boxes(boxes, iou_thresh=0.35)

    triptychs = []
    for i, b in enumerate(boxes):
        cb,_ = crop_with_pad(before, b, pad=24)
        ca,_ = crop_with_pad(after,  b, pad=24)
        cd,_ = crop_with_pad(cv2.applyColorMap(diff_u8, cv2.COLORMAP_JET), b, pad=24)
        # equalise heights for neat stacking
        target_h = 320
        def resize_to_h(img,h=target_h):
            h0,w0 = img.shape[:2]; return cv2.resize(img, (int(w0*h/h0), h), interpolation=cv2.INTER_AREA)
        cb, ca, cd = map(resize_to_h, [cb, ca, cd])
        tri = np.hstack([cb, ca, cd])
        triptychs.append((f"chg-{i+1:03d}", b, tri))
        cv2.imwrite(f"image-comparator/out/region_{i+1:03d}.png", tri)

    save_thumb("page_before.png", before)
    save_thumb("page_after.png",  after)

    # Build a manifest the model can read alongside images
    payload = {
    "page": {
        "viewport": {"w": int(before.shape[1]), "h": int(before.shape[0])},
        "before_image": "page_before.png",
        "after_image":  "page_after.png"
    },
    "changes": []
    }

    for i, (chg_id, box, tri) in enumerate(triptychs, start=1):
        fn = f"region_{i:03d}.png"
        cv2.imwrite(str(OUT / fn), tri)
        x,y,w,h = box
        payload["changes"].append({
        "id": chg_id,
        "bbox": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
        "triptych": fn
        # (optional) add local metrics if you compute them later, e.g. local_ssim, area, saliency
        })

    with open(OUT / "manifest.json", "w") as f:
        json.dump(payload, f, indent=2)
