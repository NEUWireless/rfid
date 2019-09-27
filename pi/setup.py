from setuptools import setup

setup(name='wc_attendance',
      version='0.1',
      description='Wireless Club RFID Attendance',
      url='https://github.com/thomashinds/wireless-club-rfid-attendance',
      author='NEU Wireless Club',
      author_email='none@example.com',
      license='Undecided',
      packages=['wc_attendance'],
      install_requires=[
          'gpiozero',
          'npyscreen'
      ],
      include_package_data=True,
      entry_points={
          'console_scripts': [
              'wc-attendance=wc_attendance.run_attendance:main',
              'wc-tui=wc_attendance.tui:main'
          ]
      },
      zip_safe=False)
