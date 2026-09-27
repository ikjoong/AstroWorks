"""PNG 배경 투명화 도구.

이미지 가장자리(모서리)의 색을 배경색으로 보고, 가장자리에서 이어진
비슷한 색 영역만 투명하게 바꾼다. 아이콘 내부의 같은 색은 유지된다.
"""
import os
import tkinter as tk
from collections import Counter, deque
from tkinter import filedialog, messagebox

from PIL import Image, ImageTk


def detect_bg_color(im):
    """네 모서리 중 가장 많은 색을 배경색으로 판단."""
    w, h = im.size
    corners = [im.getpixel(p) for p in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]]
    return Counter(corners).most_common(1)[0][0]


def remove_background(im, tolerance=40):
    """가장자리에서 flood fill로 배경색과 비슷한 픽셀을 투명 처리."""
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    bg = detect_bg_color(im)

    def similar(c):
        return all(abs(c[i] - bg[i]) <= tolerance for i in range(3))

    q = deque()
    for x in range(w):
        q.append((x, 0))
        q.append((x, h - 1))
    for y in range(h):
        q.append((0, y))
        q.append((w - 1, y))

    seen = set()
    while q:
        x, y = q.popleft()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h):
            continue
        seen.add((x, y))
        if not similar(px[x, y]):
            continue
        px[x, y] = (0, 0, 0, 0)
        q.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])
    return im


def checkerboard(size, cell=8):
    """투명 영역이 보이도록 체크무늬 배경 생성."""
    w, h = size
    board = Image.new("RGBA", size, (255, 255, 255, 255))
    px = board.load()
    for y in range(h):
        for x in range(w):
            if (x // cell + y // cell) % 2:
                px[x, y] = (204, 204, 204, 255)
    return board


class App:
    PREVIEW_MAX = 300

    def __init__(self, root):
        self.root = root
        self.src_path = None
        self.src_img = None
        self.result = None
        root.title("PNG 배경 투명화")

        top = tk.Frame(root, padx=10, pady=10)
        top.pack(fill="x")
        tk.Button(top, text="파일 선택...", command=self.open_file).pack(side="left")
        self.path_label = tk.Label(top, text="선택된 파일 없음", anchor="w")
        self.path_label.pack(side="left", padx=10, fill="x", expand=True)

        opt = tk.Frame(root, padx=10)
        opt.pack(fill="x")
        tk.Label(opt, text="허용 오차:").pack(side="left")
        self.tol = tk.Scale(opt, from_=0, to=128, orient="horizontal", length=200,
                            command=lambda _: self.process())
        self.tol.set(40)
        self.tol.pack(side="left")

        views = tk.Frame(root, padx=10, pady=10)
        views.pack()
        tk.Label(views, text="원본").grid(row=0, column=0)
        tk.Label(views, text="결과").grid(row=0, column=1)
        self.before = tk.Label(views, width=40, height=15, relief="sunken")
        self.after = tk.Label(views, width=40, height=15, relief="sunken")
        self.before.grid(row=1, column=0, padx=5)
        self.after.grid(row=1, column=1, padx=5)

        bottom = tk.Frame(root, padx=10, pady=10)
        bottom.pack(fill="x")
        self.save_btn = tk.Button(bottom, text="저장...", state="disabled", command=self.save)
        self.save_btn.pack(side="right")

    def open_file(self):
        path = filedialog.askopenfilename(
            title="이미지 선택",
            filetypes=[("이미지 파일", "*.png *.jpg *.jpeg *.bmp *.gif"), ("모든 파일", "*.*")],
        )
        if not path:
            return
        try:
            self.src_img = Image.open(path).convert("RGBA")
        except Exception as e:
            messagebox.showerror("오류", f"이미지를 열 수 없습니다.\n{e}")
            return
        self.src_path = path
        self.path_label.config(text=path)
        self.show(self.before, self.src_img, "_tk_before")
        self.process()

    def process(self):
        if self.src_img is None:
            return
        self.result = remove_background(self.src_img, self.tol.get())
        self.show(self.after, self.result, "_tk_after")
        self.save_btn.config(state="normal")

    def show(self, label, im, attr):
        # 작은 이미지는 확대, 큰 이미지는 축소해서 미리보기
        scale = self.PREVIEW_MAX / max(im.size)
        size = (max(1, int(im.width * scale)), max(1, int(im.height * scale)))
        view = im.resize(size, Image.NEAREST if scale > 1 else Image.LANCZOS)
        board = checkerboard(size)
        board.alpha_composite(view)
        photo = ImageTk.PhotoImage(board)
        setattr(self, attr, photo)  # 참조 유지 (GC 방지)
        label.config(image=photo, width=size[0], height=size[1])

    def save(self):
        base, _ = os.path.splitext(self.src_path)
        path = filedialog.asksaveasfilename(
            title="저장",
            initialdir=os.path.dirname(self.src_path),
            initialfile=os.path.basename(base) + "_transparent.png",
            defaultextension=".png",
            filetypes=[("PNG", "*.png")],
        )
        if not path:
            return
        self.result.save(path)
        messagebox.showinfo("완료", f"저장했습니다.\n{path}")


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
