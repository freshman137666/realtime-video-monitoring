import cv2

def test_camera_indices():
    """Iterates through camera indices and tries to open them."""
    index = 0
    while True:
        print(f"尝试打开摄像头索引: {index}")
        # 在Windows上，明确使用DSHOW后端可以提高稳定性和兼容性
        cap = cv2.VideoCapture(index + cv2.CAP_DSHOW)
        if not cap.isOpened():
            print(f"摄像头索引 {index} 打开失败或不存在。")
            if index >= 5: # 检查前6个索引
                print("\n没有找到可用的摄像头。")
                break
        else:
            print(f"成功打开摄像头索引: {index}!")
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("无法读取帧。")
                    break
                
                # 在窗口中显示摄像头画面
                # 使用英文标题避免乱码
                title = f'Camera Test (Index {index}) - Press Q to close and test next'
                cv2.imshow(title, frame)
                
                # 按 'q' 键退出当前摄像头的测试
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            cap.release()
            cv2.destroyAllWindows()
            
            # 询问用户是否继续测试下一个索引
            choice = input(f"Camera {index} test finished. Continue to next index? (y/n): ").lower()
            if choice != 'y':
                break

        index += 1

if __name__ == "__main__":
    print("开始测试摄像头...")
    test_camera_indices()
    print("\n测试结束。") 