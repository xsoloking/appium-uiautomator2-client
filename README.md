# Appium Uiautomator2 Client 

This client is a simple implementation written in Python for [appium-uiautomator2-server](https://github.com/appium/appium-uiautomator2-server), it should be easy to intergarted into other testing framework.
   
### Installation

Before using this driver, you should build, install and run [appium-uiautomator2-server](https://github.com/appium/appium-uiautomator2-server) at first.

- Building appium-uiautomator2-server project using below commands

  `./gradlew clean assembleServerDebug assembleServerDebugAndroidTest`
- Installing both src and test apks to the device and execute the instrumentation tests.

  ` adb shell am instrument -w io.appium.uiautomator2.server.test/android.support.test.runner.AndroidJUnitRunner`
- Forward tcp port 6790 to local

  ` adb forward tcp:6790 tcp:6790`

Now it is ready to control the device, below are examples
```python
client = AppiumClient()
# Click "test" on screen
client.click_element(client.find_element(ByText("test")))
# Find element by xpath, class name, resrouce id, and uiautpmator statements
client.find_element(ByXpath("//*[@class='android.widget.TextView'][1]"))
client.find_element(ByClass("android.widget.TextView"))
client.find_element(ById("android:id/text1"))
client.find_element(ByUiautomator("new UiSelector().resourceId(\"android:id/text1\")"))
# Tap (x, y)
client.tap(x, y)
```

### ToDo
This client was implemented several yesrs ago, I didn't test all the fucntions on the latest version of appium uiautomator2 server. So there might be adaption works if the service side has changes. 

License
----

MIT


**Free Software, Hell Yeah!**
