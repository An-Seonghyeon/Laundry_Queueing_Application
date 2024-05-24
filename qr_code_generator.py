import qrcode

# washer_id 예시 (실제 데이터로 대체 필요)
washer_id = '하용조관_7_2'

# URL of the webpage
url = f"laundry-queueing-application-dun.vercel.app/option?washer_id={washer_id}"

# Generate QR code
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)
qr.add_data(url)
qr.make(fit=True)

# Create an image from the QR Code instance
img = qr.make_image(fill_color="black", back_color="white")

# Save it somewhere, for example:
img_path = f"{washer_id}_qr.png"
img.save(img_path)
