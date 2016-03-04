<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:se="http://www.opengis.net/se" version="1.1.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.1.0/StyledLayerDescriptor.xsd">
  <NamedLayer>
    <se:Name>bsas_corredores</se:Name>
    <UserStyle>
      <se:Name>bsas_corredores</se:Name>
      <se:FeatureTypeStyle>
        <se:Rule>
          <se:Name>Articulacion multimodal a corredores de jerarquia internacional</se:Name>
          <se:Description>
            <se:Title>Articulacion multimodal a corredores de jerarquia internacional</se:Title>
          </se:Description>
          <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
            <ogc:PropertyIsEqualTo>
              <ogc:PropertyName>nombre</ogc:PropertyName>
              <ogc:Literal>Articulacion multimodal a corredores de jerarquia internacional</ogc:Literal>
            </ogc:PropertyIsEqualTo>
          </ogc:Filter>
          <se:LineSymbolizer>
            <se:Stroke>
              <se:SvgParameter name="stroke">#1f5eb4</se:SvgParameter>
              <se:SvgParameter name="stroke-width">3.78</se:SvgParameter>
              <se:SvgParameter name="stroke-linejoin">bevel</se:SvgParameter>
              <se:SvgParameter name="stroke-linecap">butt</se:SvgParameter>
            </se:Stroke>
          </se:LineSymbolizer>
        </se:Rule>
        <se:Rule>
          <se:Name>Articulacion multimodal a corredores de jerarquia nacional</se:Name>
          <se:Description>
            <se:Title>Articulacion multimodal a corredores de jerarquia nacional</se:Title>
          </se:Description>
          <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
            <ogc:PropertyIsEqualTo>
              <ogc:PropertyName>nombre</ogc:PropertyName>
              <ogc:Literal>Articulacion multimodal a corredores de jerarquia nacional</ogc:Literal>
            </ogc:PropertyIsEqualTo>
          </ogc:Filter>
          <se:LineSymbolizer>
            <se:Stroke>
              <se:SvgParameter name="stroke">#4e8bb4</se:SvgParameter>
              <se:SvgParameter name="stroke-width">3.78</se:SvgParameter>
              <se:SvgParameter name="stroke-linejoin">bevel</se:SvgParameter>
              <se:SvgParameter name="stroke-linecap">butt</se:SvgParameter>
            </se:Stroke>
          </se:LineSymbolizer>
          <se:LineSymbolizer>
            <VendorOption name="placement">lastPoint</VendorOption>
            <se:Stroke>
              <se:GraphicStroke>
                <se:Graphic>
                  <se:Mark>
                    <se:WellKnownName>filled_arrowhead</se:WellKnownName>
                    <se:Fill>
                      <se:SvgParameter name="fill">#4e8bb4</se:SvgParameter>
                    </se:Fill>
                    <se:Stroke>
                      <se:SvgParameter name="stroke">#000000</se:SvgParameter>
                      <se:SvgParameter name="stroke-opacity">0.00</se:SvgParameter>
                    </se:Stroke>
                  </se:Mark>
                  <se:Size>36.75</se:Size>
                </se:Graphic>
              </se:GraphicStroke>
            </se:Stroke>
          </se:LineSymbolizer>
          <se:LineSymbolizer>
            <VendorOption name="placement">firstPoint</VendorOption>
            <se:Stroke>
              <se:GraphicStroke>
                <se:Graphic>
                  <se:Mark>
                    <se:WellKnownName>filled_arrowhead</se:WellKnownName>
                    <se:Fill>
                      <se:SvgParameter name="fill">#4e8bb4</se:SvgParameter>
                    </se:Fill>
                    <se:Stroke>
                      <se:SvgParameter name="stroke">#000000</se:SvgParameter>
                      <se:SvgParameter name="stroke-opacity">0.00</se:SvgParameter>
                    </se:Stroke>
                  </se:Mark>
                  <se:Size>36.75</se:Size>
                  <se:Rotation>
                    <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
                      <ogc:Literal>180</ogc:Literal>
                    </ogc:Filter>
                  </se:Rotation>
                </se:Graphic>
              </se:GraphicStroke>
            </se:Stroke>
          </se:LineSymbolizer>
        </se:Rule>
        <se:Rule>
          <se:Name>Corredores de conexion interprovinciales y/o  nodos urbanos fortalecidos</se:Name>
          <se:Description>
            <se:Title>Corredores de conexion interprovinciales y/o  nodos urbanos fortalecidos</se:Title>
          </se:Description>
          <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
            <ogc:PropertyIsEqualTo>
              <ogc:PropertyName>nombre</ogc:PropertyName>
              <ogc:Literal>Corredores de conexion interprovinciales y/o  nodos urbanos fortalecidos</ogc:Literal>
            </ogc:PropertyIsEqualTo>
          </ogc:Filter>
          <se:LineSymbolizer>
            <se:Stroke>
              <se:SvgParameter name="stroke">#7aa097</se:SvgParameter>
              <se:SvgParameter name="stroke-width">4.2</se:SvgParameter>
              <se:SvgParameter name="stroke-linejoin">bevel</se:SvgParameter>
              <se:SvgParameter name="stroke-linecap">butt</se:SvgParameter>
            </se:Stroke>
          </se:LineSymbolizer>
        </se:Rule>
      </se:FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>