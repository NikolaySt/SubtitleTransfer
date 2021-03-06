using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using Newtonsoft.Json;

namespace SubtitleTransfer
{
	internal class Program
	{
		public class RowCaption
		{
			public int Index { get; set; }
			public TimeSpan From { get; set; }
			public TimeSpan To { get; set; }
			public string Text { get; set; }
			public RowCaption()
			{
				Text = "";
			}
		}

		public class RowTranslation
		{
			public RowCaption ForeignLang { get; set; }
			public RowCaption MotherLang { get; set; }
		}

		private static void Main(string[] args)
		{
			Console.OutputEncoding = Encoding.UTF8;
			Console.WriteLine("Transorm movie closecaptions");
			Console.WriteLine("v1");

			var baseName = "ted1";//"Green.Book";

			var path = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Subtitles");
			var foreignLang = ReadAndTransform(Path.Combine(path, $"{baseName}.en.srt"));
			Print(foreignLang);

			var motherLang = ReadAndTransform(Path.Combine(path, $"{baseName}.bg.srt"));
			Print(motherLang);

			var ccTranslate = Translate(foreignLang, motherLang);
			Print(ccTranslate);

			var outputFile = Path.Combine(path, $"{baseName}.bg.en.csv");
			if (File.Exists(outputFile))
				File.Delete(outputFile);

			SaveToCSVFile(outputFile, ccTranslate);

			outputFile = Path.Combine(path, $"{baseName}.bg.en.json");
			if (File.Exists(outputFile))
				File.Delete(outputFile);

			SaveToJson(outputFile, ccTranslate);

			Console.WriteLine("Done");
			Console.ReadLine();
		}

		/// <summary>
		/// 2
		/// 00:01:12,739 --> 00:01:15,402
		/// Cigars. Cigarettes.
		/// </summary>
		/// <param name="file"></param>
		/// <returns></returns>
		private static List<RowCaption> ReadAndTransform(string file)
		{
			var result = new List<RowCaption>();

			var lines = File.ReadAllLines(file);
			var index = 0;
			RowCaption caption = null;
			var regex = new Regex("(\\d{2}:\\d{2}:\\d{2}).*(\\d{2}:\\d{2}:\\d{2})");
			while (index < lines.Count())
			{

				var line = lines[index];
				index++;
				// Note get line index
				if (int.TryParse(line, out int lineIndex))
				{
					if (caption != null)
					{
						result.Add(caption);
					}
					// Start index
					caption = new RowCaption()
					{
						Index = lineIndex,
					};
					continue;
				}

				if (caption == null)
					continue;

				// Find time 00:01:12,739 --> 00:01:15,402
				var match = regex.Match(line);
				if (match.Success && match.Groups.Count > 1)
				{
					caption.From = TimeSpan.Parse(match.Groups[1].Value);
					caption.To = TimeSpan.Parse(match.Groups[2].Value);

					continue;
				}

				if (string.IsNullOrWhiteSpace(line))
					continue;

				// NOTE Text multilines usually two lines
				//Cigars.Cigarettes.
				if (string.IsNullOrWhiteSpace(caption.Text))
				{
					caption.Text = line;
				}
				else
				{
					caption.Text += " " + line;
				}
			}

			return result;
		}

		private static void Print(
			List<RowCaption> captions,
			int maxPrint = 20)
		{
			var index = 0;
			foreach (var caption in captions)
			{
				Console.WriteLine(caption.Index);
				Console.WriteLine($"{caption.From} --> {caption.To}");
				Console.WriteLine(caption.Text);
				Console.WriteLine("");
				Console.WriteLine("");
				index++;

				if (index > maxPrint)
					break;
			}
		}

		private static void Print(
			List<RowTranslation> captions,
			int maxPrint = 20)
		{
			var index = 0;
			foreach (var caption in captions)
			{
				Console.WriteLine($"{caption.ForeignLang.From} --> {caption.ForeignLang.To}");
				Console.WriteLine($"{caption.MotherLang.From} --> {caption.MotherLang.To}");
				Console.WriteLine(caption.ForeignLang.Text);
				Console.WriteLine(caption.MotherLang.Text);
				Console.WriteLine("");
				index++;

				if (index > maxPrint)
					break;
			}
		}

		private static List<RowTranslation> Translate(List<RowCaption> foreign, List<RowCaption> mother)
		{
			var result = new List<RowTranslation>();

			foreach (var caption in foreign)
			{
				//if (caption.Text.Length < 10)
				//	continue;

				var transalateCaption = mother.FirstOrDefault(it =>
					Math.Abs((it.From - caption.From).TotalSeconds) < 2
					&& Math.Abs((it.To - caption.To).TotalSeconds) < 2);

				if (transalateCaption != null)
				{
					var row = new RowTranslation()
					{
						ForeignLang = caption,
						MotherLang = transalateCaption
					};
					result.Add(row);
				}
			}

			return result;
		}

		private static void SaveToCSVFile(
			string file,
			List<RowTranslation> captions,
			string separate = "|")
		{
			var lines = new List<string>();

			foreach (var caption in captions)
			{
				var line =
					caption.MotherLang.Text +
					separate +
					caption.ForeignLang.Text +
					separate + "#" +
					caption.ForeignLang.From +
					separate + "#"+
					caption.ForeignLang.To;

				byte[] bytes = Encoding.Default.GetBytes(line);
				line = Encoding.UTF8.GetString(bytes);

				lines.Add(line);
			}

			File.WriteAllLines(file, lines);
		}

		private static void SaveToJson(
			string file,
			List<RowTranslation> captions)
		{
			var json = JsonConvert.SerializeObject(captions);

			File.WriteAllText(file, json);
		}
	}
}
