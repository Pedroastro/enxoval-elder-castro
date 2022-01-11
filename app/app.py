from flask import Flask, render_template, request
import mercadopago
import requests

ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"
DOMAIN = "http://enxoval-elder-castro.herokuapp.com/"


# Configure application
app = Flask(__name__)


# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Setup mercado pago sdk
sdk = mercadopago.SDK(ACCESS_TOKEN)


def apology(message):
    """Renders page with appology message"""
    return render_template("error.html", errorMessage=message)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == 'POST':
        # Check if amount inputed at home page is float
        try:
            amount = float(request.form.get("amount"))
            if amount < 0:
                return apology("Por favor digite um valor válido")
        except:
            return apology("Por favor digite um valor válido")
        preference_data = {
            "back_urls": {
                "success": "{}feedback".format(DOMAIN),
                "failure": "{}feedback".format(DOMAIN),
                "pending": "{}feedback".format(DOMAIN)
            },
            "redirect_urls": {
                "success": "{}feedback".format(DOMAIN),
                "failure": "{}feedback".format(DOMAIN),
                "pending": "{}feedback".format(DOMAIN)
            },
            "auto_return": "approved",
            "items": [
                {
                    "title": "Donation",
                    "quantity": 1,
                    "unit_price": amount
                }
            ],
            "external_reference": "Enxoval"
        }
        # Create mercado pago api preference
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]

        return render_template("donation.html", preference_id=preference["id"])
    
    else:
        #find transactions
        payments = requests.get('https://api.mercadopago.com/v1/payments/search?sort=date_created&criteria=desc&external_reference=Enxoval', headers={"Authorization": "Bearer {}".format(ACCESS_TOKEN)}).json()
        total_donation = 0
        for payment in payments["results"]:
            if payment["status"] == "approved":
                total_donation += float(payment["transaction_details"]["net_received_amount"])

        return render_template("home.html", total_donation=round(total_donation, 2))


@app.route("/feedback")
def feedback():
    """Gives the user feedback on donation"""
    donation = requests.get('https://api.mercadopago.com/v1/payments/{}'.format(request.args.get("payment_id")), headers={"Authorization": "Bearer {}".format(ACCESS_TOKEN)}).json()
    pendingStatus = ["pending", "authorized", "in_process", "in_mediation"]
    if donation["status"] == "404":
        return render_template("failure.html")
    elif donation["status"] == "500":
        return apology("Erro no servidor do Mercado Pago")
    elif donation["status"] in pendingStatus:
        return render_template("pending.html")
    elif donation["status"] == "approved":
        return render_template("success.html")
    else:
        return apology("Algo deu errado")


if __name__ == "__main__":
    app.run()
