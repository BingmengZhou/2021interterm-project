import matplotlib.pyplot as plt
import pandas as pd
from pylab import *
from xlrd import open_workbook

class chart:
    def line_chart(self):
        x_data = []
        y_data = []
        wb = open_workbook('D:/pycharm/flaskProject/data_face_detection.xlsx')

        for s in wb.sheets():
            print
            'Sheet:', s.name
            for row in range(s.nrows):
                print
                'the row is:', row
                values = []
                for col in range(s.ncols):
                    values.append(s.cell(row, col).value)
                print
                values
                x_data.append(values[0])
                y_data.append(values[1])

                plt.plot(x_data, y_data, 'bo-', label=u"Phase curve", linewidth=1)

                plt.annotate('zero point', xy=(180, 0), xytext=(60, 3),
                             arrowprops=dict(facecolor='black', shrink=0.05), )

                plt.title(u"invade data")
                plt.legend()

                ax = gca()
                ax.spines['right'].set_color('none')
                ax.spines['top'].set_color('none')
                ax.xaxis.set_ticks_position('bottom')
                ax.spines['bottom'].set_position(('data', 0))
                ax.yaxis.set_ticks_position('left')
                ax.spines['left'].set_position(('data', 0))

                plt.xlabel(u"input-deg")
                plt.ylabel(u"output-V")
                plt.savefig('D:/pycharm/flaskProject/line_face_detection.png', bbox_inches='tight')
                plt.show()

    def chart_diagram(self):
        # 读取目标表格文件，并用people代表读取到的表格数据
        people = pd.read_excel('D:/pycharm/flaskProject/data_face_detection.xlsx')
        # x轴是姓名，y轴是年龄，让直方图排序显示，默认升序
        people.sort_values(by='time', inplace=False, ascending=False)
        # 在控制台中输出表格数据
        print(people)
        # 将直方图颜色统一设置为蓝色
        people.plot.bar(x='time', y='facenum_cur', color='blue')
        # 旋转X轴标签，让其横向写
        plt.xticks(rotation=360)
        plt.show()
        plt.savefig('D:/pycharm/flaskProject/chart_face_detection.png', bbox_inches='tight')
