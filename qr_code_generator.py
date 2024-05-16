#pip install qrcode[pil]

import qrcode

# URL of the webpage
url = f"https://laundryqueueingapp-22100275-handongack-sanghoonparks-projects.vercel.app/option?washer_id={washer_id}"

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