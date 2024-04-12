import os
import sys
from PIL import Image

def convert_webp_to_jpg(directory):
    # 使用os.walk()递归遍历目录及其所有子目录
    for root, dirs, files in os.walk(directory):
        for filename in files:
            # 检查文件是否为webp格式
            if filename.endswith('.webp'):
                # 构建完整的文件路径
                file_path = os.path.join(root, filename)
                # 打开webp图片文件
                with Image.open(file_path) as img:
                    # 文件名不包括后缀
                    base_filename = filename[:-5]
                    # 构建新的jpg文件路径
                    new_file_path = os.path.join(root, base_filename + '.jpg')
                    # 转换为RGB格式（因为webp可能包含透明度）并保存为jpg
                    img.convert('RGB').save(new_file_path, 'JPEG')
                    print(f"Converted '{file_path}' to '{new_file_path}'")

def main():
    # 检查命令行参数
    if len(sys.argv) != 2:
        print("Usage: python script.py <directory_path>")
        sys.exit(1)

    directory_path = sys.argv[1]
    convert_webp_to_jpg(directory_path)

if __name__ == "__main__":
    main()

