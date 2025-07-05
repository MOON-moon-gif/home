# server.py (已修复)
import socket
import threading

# --- 配置 ---
HOST = '127.0.0.1'  # 服务器IP地址，'127.0.0.1' 表示本机
PORT = 65432  # 服务器端口号，可以选择1024到65535之间的任意数字

# --- 存储用户信息和连接 ---
# 预设的用户凭证 {用户名: 密码}
USERS = {
    'user1': '12345',
    'user2': 'abcde'
}

# 存储已登录用户的连接 {用户名: 客户端socket对象}
online_clients = {}
lock = threading.Lock()  # 用于在多线程环境下安全地访问 online_clients


def handle_client(conn, addr):
    """
    为每个客户端连接创建一个新的线程来处理。
    """
    print(f"新的连接: {addr}")
    current_user = None

    try:
        # --- 1. 登录验证 (已修复逻辑) ---
        is_logged_in = False
        while not is_logged_in:
            # 接收客户端发送的登录信息
            data = conn.recv(1024).decode('utf-8')
            if not data:
                # 客户端在登录前断开连接
                break

            try:
                username, password = data.split(':', 1)

                # 首先验证用户名和密码是否正确
                if USERS.get(username) == password:
                    # 使用锁来安全地检查和更新在线用户列表
                    with lock:
                        if username in online_clients:
                            # 如果用户已在线，发送失败消息
                            conn.sendall("登录失败: 该用户已在线。".encode('utf-8'))
                        else:
                            # 登录成功，更新在线列表
                            print(f"用户 {username} 从 {addr} 登录成功。")
                            current_user = username
                            online_clients[current_user] = conn
                            is_logged_in = True  # 标记为已登录，以退出循环
                            conn.sendall("登录成功!".encode('utf-8'))
                else:
                    # 密码或用户名错误
                    conn.sendall("登录失败: 用户名或密码错误。".encode('utf-8'))
            except ValueError:
                conn.sendall("登录失败: 发送格式不正确。".encode('utf-8'))
            except Exception as e:
                print(f"登录验证期间发生错误: {e}")
                break

        # --- 2. 消息转发 ---
        if current_user:  # 只有登录成功的用户才能进入此循环
            while True:
                # 接收消息，格式应为 "接收方:消息内容"
                message = conn.recv(1024).decode('utf-8')
                if not message:
                    break  # 客户端断开连接

                print(f"收到来自 {current_user} 的消息: {message}")

                try:
                    recipient, msg_content = message.split(':', 1)
                    forward_message = f"来自 {current_user} 的消息: {msg_content}"

                    recipient_conn = None
                    # 使用锁来安全地读取在线列表
                    with lock:
                        recipient_conn = online_clients.get(recipient)

                    if recipient_conn:
                        # 如果接收方在线，则转发消息
                        recipient_conn.sendall(forward_message.encode('utf-8'))
                    else:
                        # 如果接收方不在线或不存在
                        conn.sendall(f"系统提示: 用户 {recipient} 不在线或不存在。".encode('utf-8'))

                except ValueError:
                    conn.sendall("系统提示: 发送消息的格式不正确（应为 '接收方:消息内容'）。".encode('utf-8'))
                except Exception as e:
                    print(f"处理消息时发生错误: {e}")
                    break

    except ConnectionResetError:
        print(f"连接被客户端 {addr} 重置。")
    except Exception as e:
        print(f"与 {addr} 通信时发生错误: {e}")

    finally:
        # --- 清理工作 ---
        if current_user:
            # 使用锁来安全地移除下线的用户
            with lock:
                if current_user in online_clients:
                    del online_clients[current_user]
            print(f"用户 {current_user} 已下线。")
        conn.close()
        print(f"连接 {addr} 已关闭。")


def start_server():
    """
    启动服务器主程序
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((HOST, PORT))
    except OSError as e:
        print(f"错误：无法绑定到 {HOST}:{PORT} - {e}")
        return

    server_socket.listen()
    print(f"服务器已启动，正在监听 {HOST}:{PORT}...")

    try:
        while True:
            conn, addr = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("\n服务器正在关闭...")
    finally:
        server_socket.close()
        print("服务器已关闭。")


if __name__ == "__main__":
    start_server()
