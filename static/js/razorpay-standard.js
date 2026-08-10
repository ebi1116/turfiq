document.addEventListener("DOMContentLoaded", () => {
  const button = document.getElementById("razorpay-pay-button");
  const keySource = document.getElementById("razorpay-key-id");
  const message = document.getElementById("razorpay-payment-message");
  if (!button || !keySource) return;

  const csrf = document.cookie.split("; ").find((row) => row.startsWith("csrftoken="))?.split("=")[1] || "";
  const showMessage = (text, isError = false) => {
    message.textContent = text;
    message.classList.toggle("text-danger", isError);
    message.classList.toggle("text-success", !isError);
  };

  button.addEventListener("click", async () => {
    button.disabled = true;
    showMessage("Preparing secure checkout…");
    try {
      if (!window.Razorpay) throw new Error("Razorpay Checkout could not be loaded.");
      const orderResponse = await fetch("/api/create-order", {
        method: "POST",
        headers: {"Content-Type": "application/json", "X-CSRFToken": csrf},
        body: JSON.stringify({amount: Number(button.dataset.amount), currency: "INR"}),
      });
      const order = await orderResponse.json();
      if (!orderResponse.ok) throw new Error(order.error || "Could not create the payment order.");

      const checkout = new window.Razorpay({
        key: JSON.parse(keySource.textContent),
        amount: order.amount,
        currency: order.currency,
        order_id: order.order_id,
        name: "TurfIQ Analytics",
        description: "30 days of TurfIQ Premium",
        theme: {color: "#0dbb75"},
        modal: {ondismiss: () => { showMessage("Payment cancelled.", true); button.disabled = false; }},
        handler: async (payment) => {
          try {
            showMessage("Verifying payment…");
            const verifyResponse = await fetch("/api/verify-payment", {
              method: "POST",
              headers: {"Content-Type": "application/json", "X-CSRFToken": csrf},
              body: JSON.stringify(payment),
            });
            const result = await verifyResponse.json();
            if (!verifyResponse.ok || !result.success) throw new Error(result.error || "Payment verification failed.");
            showMessage("Payment verified. Premium is active.");
            window.location.assign(result.redirect);
          } catch (error) {
            showMessage(error.message || "Payment verification failed.", true);
            button.disabled = false;
          }
        },
      });
      checkout.on("payment.failed", (response) => {
        showMessage(response.error?.description || "Payment failed. Please try again.", true);
        button.disabled = false;
      });
      checkout.open();
    } catch (error) {
      showMessage(error.message || "Unable to start checkout.", true);
      button.disabled = false;
    }
  });
});
