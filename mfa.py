from __main__ import app
from flask import request
import smtplib
import ssl
import uuid
import sqlite3
import traceback
import schedule

PORT     = 465
SMTP_SRV = "smtp.gmail.com"
WEB_SRV  = "example.com"
SENDER   = "TODO@gmail.com"
PASSWORD = "TODO"
VALID_DURATION = 10 # in minutes
MESSAGE  = f"""Subject: MFA

The following link will be valid for {VALID_DURATION} minutes.

Link to validate the multi factor authentification : """
DB_FILENAME = 'mfa.db'

def timeout_mfa(_token):
	con = sqlite3.connect(DB_FILENAME)
	cur = con.cursor()
	cur.execute(f"DELETE FROM mfa WHERE token='{_token}'")
	con.commit()
	con.close()
	return schedule.CancelJob
		

@app.route("/mfa", methods = ['GET'])
def mfa():
	try:
		if 'mail' in request.args:
			_mail = request.args['mail']
			if 'token' in request.args:
				_token_co = request.args['token']
				print(_mail)
				# Send mail with unique token
				_token = str(uuid.uuid4())
				url = f"{WEB_SRV}/validate?token={_token}"
				
				context = ssl.create_default_context()
				with smtplib.SMTP_SSL(SMTP_SRV, PORT, context=context) as smtp:
					smtp.login(SENDER, PASSWORD)
					smtp.sendmail(SENDER, _mail, message + url)

				con = sqlite3.connect(DB_FILENAME)
				cur = con.cursor()
				cur.execute('CREATE TABLE IF NOT EXISTS mfa ("id" INTEGER PRIMARY KEY AUTOINCREMENT, "mail" TEXT, "token" TEXT, "token_co" TEXT)')
				res = cur.execute(f"SELECT * FROM mfa WHERE mail='{_mail}' AND token_co='{_token_co}'")
				f = res.fetchone()
				print(f)
				if f is None:
					cur.execute(f"INSERT INTO mfa(mail,token, token_co) VALUES ('{_mail}', '{_token}', '{_token_co}')")
				else:
					cur.execute(f"UPDATE mfa SET token='{_token}' WHERE id={f[0]}")
				con.commit()
				con.close()

				schedule.every(VALID_DURATION).minutes.do(timeout_mfa, _token)

				return '', 200

		return '', 400
	except:
		traceback.print_exc()
		return '', 400


@app.route("/validate", methods = ['GET'])
def validate():
	try:
		schedule.run_pending()
		if 'token' in request.args:
			_token = request.args['token']
			con = sqlite3.connect(DB_FILENAME)
			cur = con.cursor()
			res = cur.execute(f"SELECT token_co FROM mfa WHERE token='{_token}'")
			f = res.fetchone()
			if not (f is None):
				cur.execute('CREATE TABLE IF NOT EXISTS authenticated ("id" INTEGER PRIMARY KEY AUTOINCREMENT, "token_co" TEXT)')
				cur.execute(f"INSERT INTO authenticated(token_co) VALUES ('{f[0]}')")
			con.commit()
			con.close()				

			return '', 200

		return '', 400

	except:
		traceback.print_exc()
		return '', 400
