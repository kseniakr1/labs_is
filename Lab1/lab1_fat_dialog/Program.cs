using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace l1_fat_dialog
{
    class Program
    {
        public static string[] answers =
    {
                "That's good news",
                "I don't know exactly",
                "I'm not sure",
                "I'm sure",
                "It's hard to say",
                "Sorry, but I can't answer this question",
                "Let's talk about smth else",
                "Yes,
                "You're right",
            };
        public static string[] questions =
          {
                "Why do you think so?",
                "Do you like ice-cream?",
                "Where do you live?",
                "What's your favourite singer?",
                "Are you sure?",
                "Where do you want to go?",
                "Do you like your city?",
                "Where do you study?",
                "What languages do you speak?",
                "Is it true??",
                "What do you mean?",
            };
        public static string[] generalAnswer = { "Yes, I ","Nope, I not "};
        public static string[] time = { "months","years","weeks"};
        public static string[] whyanswers = {
            "I  don`t know.",
            "Who knows.",
            "Because.",
            "Oh, who cares...?"
        };

        static void Main(string[] args)
        {
            Random r = new Random();
            Console.WriteLine("Robot: Hello, how are you?");
            string result = "";
            while (true)
            {
                result = "Robot: ";
                string s = Console.ReadLine();
                string[] words = s.Split(' ');
                if (string.IsNullOrWhiteSpace(s))
                    Console.WriteLine("Robot: What`s new?");
                else
                {
                    if (s.Contains("?"))
                    {
                        if (s.Contains("Do") || s.Contains("Did") || s.Contains("Will") || s.Contains("Have"))
                        {
                            result += generalAnswer[r.Next(generalAnswer.Length)];
                            for (int i = 2; i < words.Length; i++)
                                result += words[i].Replace('?', '.')+" ";
                            result += "And you?";

                        }
                        else if (s.Contains("Why"))
                            result += whyanswers[r.Next(whyanswers.Length)];
                        else if (s.Contains("How long") || s.Contains("How often"))
                            result += "Hmmmm. Near " + r.Next(10)+ " " + time[r.Next(time.Length)];
                        else if (s.Contains("How"))
                            result += "O, I`m perfect.";
                        else result = answers[r.Next(answers.Length)];
                    }
                    else result += questions[r.Next(questions.Length)];
                    Console.WriteLine(result);
                }
            }
        }
    }
}
