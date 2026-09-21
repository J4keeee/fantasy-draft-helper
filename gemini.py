from google import genai


def main():
    client = genai.Client(api_key="AQ.Ab8RN6IAioGw-XkvBVo2dl85iTWXUeoBk415mYem6d6j6t_0Mg")


    interaction = client.interactions.create(
        model="gemini-3.5-flash-lite",
        input="Explain how AI works in a few words"
    )


    print(interaction.output_text)




if __name__ == '__main__':
    main()