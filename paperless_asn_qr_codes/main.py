# pylint: disable=global-statement,global-variable-undefined,global-variable-not-assigned,used-before-assignment
""" Main module for the paperless ASN QR code generator, fills the labels with content """
import argparse
import re

from reportlab.lib.units import mm
from reportlab_qrcode import QRCodeImage
from reportlab.pdfgen.canvas import Canvas

from paperless_asn_qr_codes import avery_labels


def render(c: Canvas, w, h):
    """ Render the QR code and ASN number on the label """
    global startASN
    global digits
    barcode_value = f"ASN{startASN:0{digits}d}"
    startASN = startASN + 1

    #qr_scale: float = 0.8  # Scale the qrcode on the label
    vertical_layout: bool = True # place qr_code an text above in vertical layout (for herma 10105 e.g.)

    font_size: float = 3 * mm  # Font size for the text
    margin: float = 1.75 * mm # Margin between the elements and the border of the label
    padding: float = 0.25 * mm # Padding between the label elements


    if vertical_layout:
      qr = QRCodeImage(barcode_value, size=h - font_size - 2 * margin - padding, border=0)

    # 0,0 is the lower left corner of the page
    #thus place elements from there
      qr.drawOn(c, (w - qr.width) /2, margin + font_size + padding)
      c.setFont("Helvetica", font_size)
      c.drawCentredString(w/2, margin, barcode_value)
    else:
      qr = QRCodeImage(barcode_value, size=h * 0.9)
      qr.drawOn(c, 1 * mm, h * 0.05)
      c.setFont("Helvetica", font_size)
      c.drawString(h, (h - font_size) / 2, barcode_value)
        


def main():
    """ Main function for the paperless ASN QR code generator """
    # Match the starting position parameter. Allow x:y or n
    def _start_position(arg):
        if mat := re.match(r"^(\d{1,2}):(\d{1,2})$", arg):
            return (int(mat.group(1)), int(mat.group(2)))
        if mat := re.match(r"^\d+$", arg):
            return int(arg)
        raise argparse.ArgumentTypeError("invalid value")

    # prepare a sorted list of all formats
    available_formats = list(avery_labels.labelInfo.keys())
    available_formats.sort()

    parser = argparse.ArgumentParser(
        prog="paperless-asn-qr-codes",
        description="CLI Tool for generating paperless ASN labels with QR codes",
    )
    parser.add_argument("start_asn", type=int, help="The value of the first ASN")
    parser.add_argument(
        "output_file",
        type=str,
        default="labels.pdf",
        help="The output file to write to (default: labels.pdf)",
    )
    parser.add_argument(
        "--format", "-f", choices=available_formats, default="averyL4731"
    )
    parser.add_argument(
        "--digits",
        "-d",
        default=7,
        help="Number of digits in the ASN (default: 7, produces 'ASN0000001')",
        type=int,
    )
    parser.add_argument(
        "--border",
        "-b",
        action="store_true",
        help="Display borders around labels, useful for debugging the printer alignment",
    )
    parser.add_argument(
        "--row-wise",
        "-r",
        action="store_false",
        help="Increment the ASNs row-wise, go from left to right",
    )
    parser.add_argument(
        "--num-labels",
        "-n",
        type=int,
        help="Number of labels to be printed on the sheet",
    )
    parser.add_argument(
        "--pages",
        "-p",
        type=int,
        default=1,
        help="Number of pages to be printed, ignored if NUM_LABELS is set (default: 1)",
    )
    parser.add_argument(
        "--start-position",
        "-s",
        type=_start_position,
        help="""Define the starting position on the sheet,
                eighter as ROW:COLUMN or COUNT, both starting from 1 (default: 1:1 or 1)""",
    )

    args = parser.parse_args()
    global startASN
    global digits
    startASN = int(args.start_asn)
    digits = int(args.digits)
    label = avery_labels.AveryLabel(
        args.format, args.border, topDown=args.row_wise, start_pos=args.start_position
    )
    label.open(args.output_file)

    # If defined use parameter for number of labels
    if args.num_labels:
        count = args.num_labels
    else:
        # Otherwise number of pages*labels - offset
        count = args.pages * label.across * label.down - label.position
    label.render(render, count)
    label.close()
