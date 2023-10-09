# NEW: We developed a tool named [IRIS](https://github.com/iris-mobile-accessibility-repair/iris-mobile) based on Xbot to automatically repair the color-based accessibility issues in Android apps. 

# Xbot
We have made the source code of Xbot and the corresponding dataset publicly available. We hope this project can benefit other researchers or practitioners in the field of accessibility testing of Android apps. Please feel free to contact us if you have any questions or issues. We will continue to maintain this project. Thanks for your feedback.

## Environment Configuration
* Ubuntu/Macbook
* Python: 2.7
* APKTool: 2.6.1 (Please use the newest version of APKTool)
* Android emulator provided by Android Studio 4.2.2： X86_64, Android 7.1.1, Google APIs, 1920 * 1080
* Android environment: adb, aapt (important)
* Java environment (jdk): jdk1.8.0_45
* Open ~/.bashrc and configure the path of JDK and SDK (Replace by your own paths):
```
export JAVA_HOME=/usr/lib/jvm/jdk1.8.0_45
export JAVA_BIN=/usr/lib/jvm/jdk1.8.0_45/bin
export CLASSPATH=.:${JAVA_HOME}/lib/dt.jar:${JAVA_HOME}/lib/tools.jar
export PATH=$PATH:${JAVA_HOME}/bin
export PATH=$PATH:/home/dell/Android/Sdk/tools
export PATH=$PATH:/home/dell/Android/Sdk/platform-tools
export PATH=$PATH:/home/dell/Android/Sdk/emulator
export JAVA_HOME JAVA_BIN CLASSPATH PATH 
```

## Accessibility Scanner Configuration

https://user-images.githubusercontent.com/23289910/186054800-5ae10f00-b19e-44e3-801b-7f4d85336efc.mp4

## Usage
Python run_xbot.py [emulator_name] [apk(s)_folder]

## Execution Record

https://user-images.githubusercontent.com/23289910/186335738-18a6838c-1176-4af1-957e-c971d73a3737.mp4

## Website
Accessibility issue gallery and samples:
https://sites.google.com/view/mobile-accessibility/

## Paper
[1] Accessible or Not? An Empirical Investigation of Android App Accessibility
```
@inproceedings{chen2019storydroid,
  title={Accessible or Not? An Empirical Investigation of Android App Accessibility},
  author={Chen, Sen and Chen, Chunyang and Fan, Lingling and Fan, Mingming and Zhan, Xian and Liu, Yang},
  booktitle={IEEE Transactions on Software Engineering (TSE)},
  year={2021},
  organization={IEEE}
}
```
## Contact
[Sen Chen](https://sen-chen.github.io/) All Copyright Reserved.
