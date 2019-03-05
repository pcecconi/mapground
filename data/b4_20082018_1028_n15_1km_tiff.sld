<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:se="http://www.opengis.net/se" xmlns:ogc="http://www.opengis.net/ogc" version="1.1.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.1.0/StyledLayerDescriptor.xsd">
  <NamedLayer>
    <se:Name>Default</se:Name>
    <UserStyle>
      <se:Name>Heladas</se:Name>
      <se:FeatureTypeStyle>
        <se:Rule>
          <se:RasterSymbolizer>
            <se:Geometry>
              <ogc:PropertyName>grid</ogc:PropertyName>
            </se:Geometry>
            <se:Opacity>1</se:Opacity>
              <se:ColorMap>
                <se:ColorMapEntry color="#b1afbe" label="Nube" opacity="1.0" quantity="-10"/>
                <se:ColorMapEntry color="#08315f" label="-8" opacity="1.0" quantity="-8"/>
                <se:ColorMapEntry color="#2767aa" label="-6" opacity="1.0" quantity="-6"/>
                <se:ColorMapEntry color="#95c6dd" label="-4" opacity="1.0" quantity="-4"/>
                <se:ColorMapEntry color="#d2e6f0" label="-2" opacity="1.0" quantity="-2"/>
                <se:ColorMapEntry color="#afdea7" label="0" opacity="1.0" quantity="0"/>
                <se:ColorMapEntry color="#f9f9f9" label="&gt;2" opacity="1.0" quantity="inf"/>
              </se:ColorMap>
          </se:RasterSymbolizer>
        </se:Rule>
      </se:FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>