# client.py
import socket
import threading

# --- 配置 ---
HOST = '127.0.0.1'  # 必须与服务器的IP地址相同
PORT = 65432  # 必须与服务器的端口号相同


def receive_messages(client_socket):
    """
    在一个独立的线程中运行，用于持续接收并显示来自服务器的消息。
    """
    while True:
        try:
            # 接收来自服务器的消息
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                print(f"\n{message}\n> ", end="")  # 打印消息并重新显示输入提示符
            else:
                # 服务器关闭了连接
                print("\n与服务器的连接已断开。")
                break
        except ConnectionResetError:
            print("\n与服务器的连接已断开。")
            break
        except Exception as e:
            print(f"\n接收消息时出错: {e}")
            break


def start_client():
    """
    启动客户端主程序
    """
    # 创建一个TCP/IP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 连接服务器
    try:
        client_socket.connect((HOST, PORT))
        print(f"已成功连接到服务器 {HOST}:{PORT}")
    except ConnectionRefusedError:
        print("连接服务器失败。请确保服务器正在运行。")
        return
    except Exception as e:
        print(f"连接时发生错误: {e}")
        return

    # --- 1. 登录流程 ---
    while True:
        username = input("请输入用户名: ")
        password = input("请输入密码: ")

        # 将用户名和密码按 "用户名:密码" 的格式发送给服务器
        credentials = f"{username}:{password}"
        client_socket.sendall(credentials.encode('utf-8'))

        # 接收服务器的登录响应
        response = client_socket.recv(1024).decode('utf-8')
        print(f"服务器响应: {response}")

        if response == "登录成功!":
            break  # 登录成功，跳出循环
        # 如果登录失败，循环将继续，提示用户重新输入

    # --- 2. 聊天流程 ---
    print("\n登录成功！现在您可以开始聊天了。")
    print("发送消息格式: '对方用户名:消息内容'")
    print("输入 'exit' 退出程序。")

    # 创建并启动一个线程来接收消息
    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    receive_thread.daemon = True
    receive_thread.start()

    # 主线程用于发送消息
    while True:
        try:
            message_to_send = input("> ")
            if message_to_send.lower() == 'exit':
                break

            # 检查消息格式是否正确
            if ':' not in message_to_send:
                print("格式错误! 请使用 '对方用户名:消息内容' 的格式。")
                continue

            # 发送消息到服务器
            client_socket.sendall(message_to_send.encode('utf-8'))

        except (EOFError, KeyboardInterrupt):
            print("\n正在退出...")
            break
        except Exception as e:
            print(f"发送消息时发生错误: {e}")
            break

    # 关闭客户端 socket
    client_socket.close()
    print("已从服务器断开连接。")


if __name__ == "__main__":
    start_client()
