from Flask_Cinema_Site import app
from Flask_Cinema_Site.models import Transaction, Viewing
from Flask_Cinema_Site.helper_functions import send_email_with_attachment

from flask import render_template, current_app

from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.platypus import Table, TableStyle

import os
import jwt
import textwrap


def generate_receipt_pdf(transaction, email_address):
    viewing = transaction.viewings[0]

    c = canvas.Canvas(transaction.get_receipt_path())
    width, height = letter
    margin = 50

    logo_path = os.path.join(current_app.root_path, "bookings", "static", 'img', 'moviebox.png')
    c.drawImage(logo_path, width / 2 - 240 / 2, 750, width=240, height=41, mask='auto')

    c.setFont('Helvetica', 30)
    c.drawString(margin, 720, 'Tickets')

    viewing_section_height = draw_movie_viewing_section(c, margin, 700, viewing, email_address)
    draw_transaction_section(c, 370, 700, transaction)

    qr_data = jwt.encode(
        payload={'transaction_id': transaction.id, 'viewing_id': viewing.id},
        key=app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    # 180 = qr code height
    draw_qr_code(c, margin, 700 - 180 - viewing_section_height, qr_data)

    # 180 = qr code height, 22 = qr code border width
    draw_seats_table(c, width - margin, 410 + 180 - 22, transaction)

    c.save()

    send_email_with_attachment(
        subject=f'[MovieBox] Your tickets for {viewing.movie.name}',
        sender=app.config['MAIL_USERNAME'],
        recipients=[email_address],
        text_body=render_template('email/receipt.txt', viewing=viewing),
        html_body=render_template('email/receipt.txt', viewing=viewing),
        file_path=transaction.get_receipt_path(),
        content_type='application/pdf',
        attachment_name='tickets.pdf'
    )


def draw_movie_viewing_section(c, x, y, viewing: Viewing, email_address):
    second_margin = x + 100
    c.setFont('Helvetica', 15)
    lp = LinePosition(y, 20)

    c.drawString(x, lp.get_current_line_y(), 'Movie:')
    # Split long names into new lines
    name_parts = textwrap.wrap(viewing.movie.name, width=22)
    for part in name_parts:
        c.drawString(second_margin, lp.get_current_line_y(), part)
        lp.inc_line_number()

    # Viewing section
    viewing_x = x + 10
    c.drawString(x, lp.get_current_line_y(), 'Viewing:')
    lp.inc_line_number()

    c.drawString(viewing_x, lp.get_current_line_y(), 'Number:')
    c.drawString(second_margin, lp.get_current_line_y(), str(viewing.id))
    lp.inc_line_number()

    c.drawString(viewing_x, lp.get_current_line_y(), 'Date:')
    c.drawString(second_margin, lp.get_current_line_y(), viewing.time.strftime('%d/%m/%y'))
    lp.inc_line_number()

    c.drawString(viewing_x, lp.get_current_line_y(), 'Time:')
    c.drawString(second_margin, lp.get_current_line_y(), viewing.time.strftime('%H:%M'))
    lp.inc_line_number()

    c.drawString(viewing_x, lp.get_current_line_y(), 'Screen:')
    c.drawString(second_margin, lp.get_current_line_y(), viewing.screen.name)
    lp.inc_line_number()

    # Email
    c.drawString(x, lp.get_current_line_y(), 'Email:')
    # Split long emails into new lines
    email_parts = textwrap.wrap(email_address, width=22)
    for part in email_parts:
        c.drawString(second_margin, lp.get_current_line_y(), part)
        lp.inc_line_number()

    return y - lp.get_current_line_y()


def draw_transaction_section(c, x, y, transaction: Transaction):
    second_margin = x + 100
    c.setFont('Helvetica', 15)

    transaction_offset = 10
    c.drawString(x, y, 'Transaction details:')

    c.drawString(x + transaction_offset, y - 20, 'Number:')
    c.drawString(second_margin, y - 20, str(transaction.id))

    c.drawString(x + transaction_offset, y - 20 * 2, 'Date:')
    c.drawString(second_margin, y - 20 * 2, transaction.datetime.strftime('%d/%m/%y'))

    c.drawString(x + transaction_offset, y - 20 * 3, 'Time:')
    c.drawString(second_margin, y - 20 * 3, transaction.datetime.strftime('%H:%M'))


def draw_seats_table(c, x, y, transaction: Transaction):
    table_style = TableStyle(
        [
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, -1), colors.gray),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ]
    )

    table_data = [
        ['Seat number', 'Ticket type', 'Price']
    ]
    for seat in transaction.seats:
        table_data.append([
            seat.seat_number,
            seat.ticket_type.name,
            '£{:.2f}'.format(seat.ticket_type.price)
        ])
    table_data.append([[]])
    table_data.append([
        'VAT',
        '',
        '£{:.2f}'.format(transaction.get_cost() * 0.2)
    ])
    table_data.append([
        'Total',
        '',
        '£{:.2f}'.format(transaction.get_cost())
    ])

    f = Table(table_data, style=table_style)
    f.wrapOn(c, 400, 100)
    table_width, table_height = f.wrap(0, 0)

    # Magic numbers 17 just works lol, 715 is the height of the top of 'Movie:'
    f.drawOn(c, x - table_width - 17, y - table_height)


def draw_qr_code(c, x, y, qr_data):
    # QR code
    qr_code = QrCodeWidget(qr_data)
    bounds = qr_code.getBounds()

    qr_width = bounds[2] - bounds[0]
    qr_height = bounds[3] - bounds[1]

    # 180 = new height and width
    d = Drawing(180, 180, transform=[180. / qr_width, 0, 0, 180. / qr_height, 0, 0])
    d.add(qr_code)

    # 22 = qr code border width
    renderPDF.draw(d, c, x - 22, y)


class LinePosition:
    def __init__(self, y, line_height):
        self.y = y
        self.line_height = line_height
        self.line_number = 0

    def get_current_line_y(self):
        return self.y - self.line_height * self.line_number

    def inc_line_number(self):
        self.line_number += 1
