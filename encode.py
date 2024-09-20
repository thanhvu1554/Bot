import logging
import base64
import io
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from Crypto.Cipher import AES
from binascii import unhexlify, hexlify
import morse3 as morse
import heapq
from collections import defaultdict

# Token của bot
TOKEN = '5452812723:AAHwdHJSMqqb__KzcSIOdJ3QuhqsIr9YTro'

# Thiết lập logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Huffman coding implementation
class HuffmanCoding:
    def build_frequency_dict(self, text):
        frequency = defaultdict(int)
        for character in text:
            frequency[character] += 1
        return frequency

    def build_huffman_tree(self, frequency):
        heap = [[weight, [char, ""]] for char, weight in frequency.items()]
        heapq.heapify(heap)
        while len(heap) > 1:
            lo = heapq.heappop(heap)
            hi = heapq.heappop(heap)
            for pair in lo[1:]:
                pair[1] = '0' + pair[1]
            for pair in hi[1:]:
                pair[1] = '1' + pair[1]
            heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:]])
        return sorted(heapq.heappop(heap)[1:], key=lambda p: (len(p[-1]), p))

    def huffman_encoding(self, text):
        frequency = self.build_frequency_dict(text)
        huffman_tree = self.build_huffman_tree(frequency)
        huff_dict = {char: code for char, code in huffman_tree}
        encoded_text = ''.join(huff_dict[char] for char in text)
        return encoded_text, huff_dict

    def huffman_decoding(self, encoded_text, huff_dict):
        reverse_huff_dict = {v: k for k, v in huff_dict.items()}
        current_code = ""
        decoded_text = ""
        for bit in encoded_text:
            current_code += bit
            if current_code in reverse_huff_dict:
                decoded_text += reverse_huff_dict[current_code]
                current_code = ""
        return decoded_text

# Mã hóa và giải mã AES cho dữ liệu
def encode_aes(data, key):
    cipher = AES.new(key.encode('utf-8'), AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(data.encode())
    return hexlify(cipher.nonce + tag + ciphertext).decode('utf-8')

def decode_aes(data, key):
    raw = unhexlify(data)
    nonce = raw[:16]
    tag = raw[16:32]
    ciphertext = raw[32:]
    cipher = AES.new(key.encode('utf-8'), AES.MODE_EAX, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')

# Mã hóa file âm thanh
def encrypt_audio(update: Update, context: CallbackContext) -> None:
    try:
        # Lấy file âm thanh từ người dùng
        file = update.message.document.get_file()
        file_data = file.download_as_bytearray()

        # Tạo khóa AES (16 bytes)
        key = "mysecretpassword".ljust(16)
        cipher = AES.new(key.encode('utf-8'), AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(file_data)

        # Gộp nonce, tag và ciphertext
        encrypted_data = cipher.nonce + tag + ciphertext

        # Lưu vào file văn bản
        bio = io.BytesIO(hexlify(encrypted_data).decode('utf-8').encode())
        bio.name = "encrypted_audio.txt"
        bio.seek(0)

        update.message.reply_document(document=bio)
    
    except Exception as e:
        update.message.reply_text(f"Đã có lỗi xảy ra: {str(e)}")

# Giải mã file âm thanh
def decrypt_audio(update: Update, context: CallbackContext) -> None:
    try:
        # Lấy file văn bản chứa dữ liệu mã hóa từ người dùng
        file = update.message.document.get_file()
        file_data = file.download_as_bytearray()

        # Tạo khóa AES (16 bytes)
        key = "mysecretpassword".ljust(16)
        raw_data = unhexlify(file_data.decode('utf-8'))

        nonce = raw_data[:16]
        tag = raw_data[16:32]
        ciphertext = raw_data[32:]

        cipher = AES.new(key.encode('utf-8'), AES.MODE_EAX, nonce=nonce)
        decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)

        # Trả lại file âm thanh gốc
        bio = io.BytesIO(decrypted_data)
        bio.name = "decrypted_audio.mp3"
        bio.seek(0)

        update.message.reply_document(document=bio)
    
    except Exception as e:
        update.message.reply_text(f"Đã có lỗi xảy ra: {str(e)}")

# Command encode
def encode_command(update: Update, context: CallbackContext) -> None:
    try:
        encode_type = context.args[0].lower()
        value = ' '.join(context.args[1:])
        
        if encode_type == 'base64':
            encoded = base64.b64encode(value.encode()).decode()
        elif encode_type == 'aes':
            key = "mysecretpassword"  # Khóa cho AES
            encoded = encode_aes(value, key)
        elif encode_type == 'morse':
            encoded = morse.encode(value)
        elif encode_type == 'huffman':
            huffman = HuffmanCoding()
            encoded, _ = huffman.huffman_encoding(value)
        else:
            update.message.reply_text(f"Loại mã hóa '{encode_type}' không được hỗ trợ.")
            return
        
        update.message.reply_text(f"<b>Encoded:</b> <code>{encoded}</code>", parse_mode=ParseMode.HTML)
    
    except Exception as e:
        update.message.reply_text(f"Đã có lỗi xảy ra: {str(e)}")

# Command decode
def decode_command(update: Update, context: CallbackContext) -> None:
    try:
        value = ' '.join(context.args)
        decoded = None
        
        # Try to decode using different methods
        try:
            decoded = base64.b64decode(value.encode()).decode()
        except:
            pass

        if decoded is None:
            try:
                decoded = decode_aes(value, "mysecretpassword")
            except:
                pass

        if decoded is None:
            try:
                decoded = morse.decode(value)
            except:
                pass

        if decoded is None:
            try:
                huffman = HuffmanCoding()
                decoded = huffman.huffman_decoding(value, huff_dict_global)
            except:
                pass

        if decoded:
            update.message.reply_text(f"<b>Decoded:</b> <code>{decoded}</code>", parse_mode=ParseMode.HTML)
        else:
            update.message.reply_text("Không thể giải mã dữ liệu được cung cấp.")
    
    except Exception as e:
        update.message.reply_text(f"Đã có lỗi xảy ra: {str(e)}")

def start_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Chào mừng bạn đến với bot mã hóa và giải mã!\n"
        "Sử dụng các lệnh sau:\n"
        "/encode <loại mã hóa> <giá trị cần mã hóa>\n"
        "/decode <giá trị cần giải mã>\n"
        "/encrypt_audio để mã hóa file âm thanh\n"
        "/decrypt_audio để giải mã file âm thanh\n"
        "Gửi hình ảnh để mã hóa hoặc tệp văn bản hoặc file mã hóa để giải mã hình ảnh."
    )

def main() -> None:
    """Khởi động bot"""
    updater = Updater(TOKEN)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("encode", encode_command))
    dispatcher.add_handler(CommandHandler("decode", decode_command))
    dispatcher.add_handler(CommandHandler("encrypt_audio", encrypt_audio))
    dispatcher.add_handler(CommandHandler("decrypt_audio", decrypt_audio))
    dispatcher.add_handler(MessageHandler(Filters.photo, handle_image))
    dispatcher.add_handler(MessageHandler(Filters.document.mime_type("text/plain"), handle_decode_image_file))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
