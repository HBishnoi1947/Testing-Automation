from selenium import webdriver
import time
import json

driver = webdriver.Chrome()
driver.get("https://chromewebstore.google.com/?hl=en")

# Inject JS to track clicks and store info globally
driver.execute_script("""
window.clickedElementInfo = null;
document.addEventListener('click', function(event) {
    const el = event.target;
    const attrs = {};
    for (let attr of el.attributes) {
        attrs[attr.name] = attr.value;
    }
    window.clickedElementInfo = {
        tag: el.tagName,
        id: el.id,
        class: el.className,
        attributes: attrs,
        text: el.innerText.slice(0, 100) // limit text size
    };
});
""")

print("Click anywhere on the webpage...")
while True:
    time.sleep(1)
    data = driver.execute_script("return window.clickedElementInfo;")
    if data:
        print(json.dumps(data, indent=2))
        # Optional: save to DB here
        driver.execute_script("window.clickedElementInfo = null;")  # reset
