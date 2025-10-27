import streamlit as st
def render_home():
  st.set_page_config(
    page_title="Home — Example App",
    page_icon="🏠",
    layout="wide",
  )

  # --- Top section ---
  st.title("Welcome to Example App")
  st.subheader("A simple, generic homepage built with Streamlit")
  st.write(
    "This is a starter landing page you can adapt for your product, portfolio, or project. "
    "Use the blocks below to highlight features, show metrics, and collect contact info."
  )

  # --- Hero with image and CTA ---
  left, right = st.columns([2, 1])
  with left:
    st.markdown("### Ready to get started?")
    st.write(
      "Try the demo, read the docs, or sign up for early access. "
      "This template demonstrates layout patterns and basic interactions."
    )
    c1, c2 = st.columns(2)
    if c1.button("Get started (Demo)"):
      st.info("Redirecting to demo... (replace with real navigation)")
    if c2.button("Learn more"):
      st.info("Open docs... (replace with real navigation)")
  with right:
    st.image("https://picsum.photos/400/250", caption="Example hero image", use_column_width=True)

  st.markdown("---")

  # --- Features ---
  st.header("Features")
  f1, f2, f3 = st.columns(3)
  f1.metric("Uptime", "99.99%")
  f2.metric("Latency", "120 ms")
  f3.metric("Users", "1.2k")

  col1, col2, col3 = st.columns(3)
  with col1:
    st.subheader("Fast")
    st.write("Low-latency responses and optimized workflows.")
  with col2:
    st.subheader("Reliable")
    st.write("Designed for stability and predictable behavior.")
  with col3:
    st.subheader("Secure")
    st.write("Security best practices built in from the ground up.")

  st.markdown("---")

  # --- Use cases / cards ---
  st.header("Use cases")
  c1, c2 = st.columns(2)
  with c1:
    st.info("Product teams can prototype landing pages and feature lists quickly.")
    st.write("- Showcase product features\n- Collect interest\n- Iterate rapidly")
  with c2:
    st.success("Engineers can embed live demos and examples.")
    st.write("- Component previews\n- Interactive forms\n- Metrics and monitoring")

  st.markdown("---")

  # --- Contact form ---
  st.header("Contact")
  with st.form("contact_form", clear_on_submit=True):
    name = st.text_input("Name")
    email = st.text_input("Email")
    message = st.text_area("Message")
    submitted = st.form_submit_button("Send message")
    if submitted:
      # Replace with real backend handling in production
      st.success("Thanks — your message has been recorded.")
      st.write("Name:", name)
      st.write("Email:", email)
      st.write("Message:", message)

  st.markdown("---")

  # --- Footer ---
  st.write(
    "Built with Streamlit • "
    "[GitHub](https://github.com/) • "
    "© " + str(st.session_state.get("year", 2025))
  )


if __name__ == "__main__":
  render_home()