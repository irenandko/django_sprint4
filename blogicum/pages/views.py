from django.shortcuts import render


def about(request):
    template = 'pages/about.html'   # change path
    return render(request, template)


def rules(request):
    template = 'pages/rules.html'   # change path
    return render(request, template)
