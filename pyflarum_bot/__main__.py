import typing as t

from pathlib import Path
from threading import Thread
from jinja2 import Environment, PackageLoader

from pyflarum.client.extensions.watch import WatchFlarumUserMixin
from pyflarum.client.extensions.absolutely_all import AbsolutelyAllFlarumUserMixin
from pyflarum.client.extensions.commands import CommandsFlarumUserMixin

from pyflarum.client.flarum.core.notifications import Notification
from pyflarum.client.flarum.core.posts import PreparedPost


FILES_PATH = Path(__file__).parent / "files"
TEMPLATE_ENV = Environment(loader=PackageLoader('pyflarum_bot', "files"))



class FlarumBot(WatchFlarumUserMixin, CommandsFlarumUserMixin, AbsolutelyAllFlarumUserMixin):
    """
        A subclass of some extensions, extended with bot capabilities.
    """


    def listen(self, check_every: float=10) -> t.NoReturn:
        """
            Starts the bot and makes it listens for new discussions, posts and messages on the forum.
        """

        self.watch_notifications(on_notification=self.process_notification, interval=check_every)



    def process_notification(self, notification: Notification) -> None:
        """
            Processes a notification.
        """

        subject = notification.get_subject()

        if hasattr(subject, 'content') and isinstance(subject.content, str):
            command = self.parse_as_command(subject.content)

            match command[0].lower():
                case 'export':
                    def _export():
                        to_export = subject.get_discussion()

                        post = PreparedPost(user=self, discussion=to_export, content=f"Exporting discussion...").post()
                        print(f"Exporting post `{to_export.id}`...")
        
                        exported_html = TEMPLATE_ENV.get_template('discussion_export.html').render(discussion=to_export.get_full_data(), all_posts=self.get_all_posts_from_discussion)
                        with open(FILES_PATH / "exports" / f"discussion-{to_export.id}.html", 'w') as export_file:
                            export_file.write(exported_html)

                        post.edit(PreparedPost(user=self, discussion=to_export, content=f"Sucessfuly exported this discussion to a file at server."))
                        return print(f"Exported post `{to_export.id}`!")

                    Thread(target=_export).start()

        else:
            return print("That notification doesn't have a content attribute, or it's not a string.")



if __name__ == '__main__':
    import os
    import dotenv
    dotenv.load_dotenv()

    BOT = FlarumBot(forum_url=os.environ['forum_url'], username_or_email=os.environ['account_username'], password=os.environ['account_password'])
    print("Listening...")
    BOT.listen()
