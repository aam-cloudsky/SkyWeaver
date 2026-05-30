from skyweaver.application.legacy.routes_app import RoutesApp

app = RoutesApp(cell_size=100.0)
app.setup()  # prepara fontes, domínio, grid, rotas, e abre a viz
