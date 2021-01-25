
@dog_name_space.route('/mail')
class Email(Resource):
    @staticmethod
    def get():
        '''Email 전송 테스트 API'''
        smtp = smtplib.SMTP('smtp.gmail.com', 587)
        smtp.ehlo()
        smtp.starttls()
        smtp.login('pknb321@gmail.com', "12281228a!")
        msg = MIMEMultipart()
        msg['Subject'] = 'Email Test Test Test'
        part = MIMEText('SMTP Email Body')
        msg.attach(part)
        msg['To'] = 'pknb213@naver.com'
        smtp.sendmail('pknb321@gmail.com', 'pknb213@naver.com', msg.as_string())

        return Response("200")


@cat_name_space.route('/info')
class HelloRedis(Resource):
    @staticmethod
    def get():
        '''Redis Information 조회'''
        return info_redis()


@cat_name_space.route('/test/<string:todo_id>')
class TodoTest(Resource):
    @staticmethod
    def get(todo_id):
        '''Hello Get URL Parameter Test'''
        print("Hello~", todo_id)
        return Response("200")

