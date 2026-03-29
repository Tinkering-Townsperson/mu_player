from flask import (  # noqa
	Blueprint, render_template, url_for
)

import qrcode
import qrcode.image.svg
from .config import get_ip_address

bp = Blueprint("connect", __name__, url_prefix="/connect")


@bp.route("/")
def index():
	data = f"http://{get_ip_address()}:5000/player"
	qr = qrcode.make(data, image_factory=qrcode.image.svg.SvgPathImage)
	qrdata = qr.to_string().decode(encoding="utf-8", errors="strict")

	bodytext = f"""
	<p class="subtitle is-4">to gain access on a different device:</p>
	<p class="subtitle is-5 has-text-centered">go to<br /><a href="{data}" target="_blank">{data}</a><br />or scan the QR code below</p>
	<div class="qr-code">
		{qrdata}
	</div>
	""" if get_ip_address else """
	<p class="subtitle is-4">IP address not configured</p>
	<p class="subtitle is-5">Make sure your computer is connected to a network and try again.</p>
	"""  # noqa

	return render_template("connect.html", bodytext=bodytext)
