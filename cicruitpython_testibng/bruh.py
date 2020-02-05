import board
import digitalio
import busio

print("bruh1")
pin = digitalio.DigitalInOut(board.D4)
print("bruh1")

spi = busio.SPI(board.SCLK, board.MOSI, board.MISO)
print("bruh3")
